from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from backend.app.core.config import get_settings
from backend.app.mappings import CANONICAL_FIELDS


DEEPSEEK_COMPLETIONS_PATH = "/chat/completions"


@dataclass(slots=True)
class LLMMappingResult:
    raw_header_signature: str
    canonical_field: str | None
    confidence: float | None
    candidate_fields: list[str]
    status: str
    reason: str


async def map_header_with_llm(
    raw_header_signature: str,
    region: str | None = None,
) -> LLMMappingResult:
    settings = get_settings()
    if not settings.enable_llm_fallback:
        return LLMMappingResult(
            raw_header_signature=raw_header_signature,
            canonical_field=None,
            confidence=None,
            candidate_fields=[],
            status="disabled",
            reason="LLM fallback is disabled.",
        )
    if not settings.deepseek_api_key:
        return LLMMappingResult(
            raw_header_signature=raw_header_signature,
            canonical_field=None,
            confidence=None,
            candidate_fields=[],
            status="skipped_no_api_key",
            reason="DeepSeek API key is not configured.",
        )

    payload = {
        "model": settings.deepseek_model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是社保表头归一化助手。"
                    "只能从给定标准字段集合中选择候选字段，"
                    "返回 JSON，字段包括 canonical_field, confidence, candidate_fields, reason。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "region": region,
                        "raw_header_signature": raw_header_signature,
                        "canonical_fields": sorted(CANONICAL_FIELDS),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }

    try:
        async with httpx.AsyncClient(base_url=settings.deepseek_api_base_url, timeout=20.0) as client:
            response = await client.post(
                DEEPSEEK_COMPLETIONS_PATH,
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return LLMMappingResult(
            raw_header_signature=raw_header_signature,
            canonical_field=None,
            confidence=None,
            candidate_fields=[],
            status="error",
            reason=str(exc),
        )

    return _parse_llm_response(raw_header_signature, response.json())


def _parse_llm_response(raw_header_signature: str, payload: dict[str, Any]) -> LLMMappingResult:
    try:
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return LLMMappingResult(
            raw_header_signature=raw_header_signature,
            canonical_field=None,
            confidence=None,
            candidate_fields=[],
            status="invalid_response",
            reason="DeepSeek returned an invalid response payload.",
        )

    canonical_field = parsed.get("canonical_field")
    candidate_fields = [field for field in parsed.get("candidate_fields", []) if field in CANONICAL_FIELDS]
    confidence = parsed.get("confidence")
    if canonical_field not in CANONICAL_FIELDS:
        canonical_field = None
    if canonical_field and canonical_field not in candidate_fields:
        candidate_fields.insert(0, canonical_field)

    return LLMMappingResult(
        raw_header_signature=raw_header_signature,
        canonical_field=canonical_field,
        confidence=float(confidence) if confidence is not None else None,
        candidate_fields=candidate_fields,
        status="success",
        reason=str(parsed.get("reason", "")),
    )
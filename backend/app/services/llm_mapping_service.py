from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from backend.app.core.config import get_settings
from backend.app.mappings import CANONICAL_FIELDS


DEEPSEEK_COMPLETIONS_PATH = "/chat/completions"
DEFAULT_LLM_TIMEOUT = 45.0


def _coerce_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return _normalize_confidence(numeric)

    candidate = str(value).strip().lower()
    if not candidate:
        return None

    text_mappings = {
        'very_high': 0.98,
        'high': 0.92,
        'medium': 0.75,
        'low': 0.45,
        'very_low': 0.2,
    }
    if candidate in text_mappings:
        return text_mappings[candidate]

    percent_candidate = candidate[:-1].strip() if candidate.endswith('%') else candidate
    try:
        numeric = float(percent_candidate)
    except ValueError:
        return None

    if candidate.endswith('%') or numeric > 1.0:
        numeric = numeric / 100.0
    return _normalize_confidence(numeric)


def _normalize_confidence(value: float) -> float | None:
    if value < 0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


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
    skipped = _build_skip_result(raw_header_signature, settings)
    if skipped is not None:
        return skipped

    payload = _build_request_payload(raw_header_signature, region=region, model=settings.deepseek_model)
    try:
        async with httpx.AsyncClient(base_url=settings.deepseek_api_base_url, timeout=DEFAULT_LLM_TIMEOUT) as client:
            response = await client.post(
                DEEPSEEK_COMPLETIONS_PATH,
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return _error_result(raw_header_signature, exc)

    return _parse_llm_response(raw_header_signature, response.json())


def map_header_with_llm_sync(
    raw_header_signature: str,
    region: str | None = None,
) -> LLMMappingResult:
    settings = get_settings()
    skipped = _build_skip_result(raw_header_signature, settings)
    if skipped is not None:
        return skipped

    payload = _build_request_payload(raw_header_signature, region=region, model=settings.deepseek_model)
    try:
        with httpx.Client(base_url=settings.deepseek_api_base_url, timeout=DEFAULT_LLM_TIMEOUT) as client:
            response = client.post(
                DEEPSEEK_COMPLETIONS_PATH,
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return _error_result(raw_header_signature, exc)

    return _parse_llm_response(raw_header_signature, response.json())


def _build_request_payload(raw_header_signature: str, *, region: str | None, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是社保和公积金表头归一化助手。"
                    "你只能从给定标准字段集合里选择候选字段，"
                    "必须返回 JSON，字段包括 canonical_field, confidence, candidate_fields, reason。"
                    "如果不能确定，就把 canonical_field 设为 null，并给出候选字段排序。"
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


def _extract_json_content(content: Any) -> str:
    if isinstance(content, list):
        text = ''.join(part.get('text', '') if isinstance(part, dict) else str(part) for part in content)
    else:
        text = str(content)
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fenced:
        return fenced.group(1)
    return stripped


def _build_skip_result(raw_header_signature: str, settings) -> LLMMappingResult | None:
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
    return None


def _error_result(raw_header_signature: str, exc: Exception) -> LLMMappingResult:
    return LLMMappingResult(
        raw_header_signature=raw_header_signature,
        canonical_field=None,
        confidence=None,
        candidate_fields=[],
        status="error",
        reason=str(exc),
    )


def _parse_llm_response(raw_header_signature: str, payload: dict[str, Any]) -> LLMMappingResult:
    try:
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(_extract_json_content(content))
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
        confidence=_coerce_confidence(confidence),
        candidate_fields=candidate_fields,
        status="success",
        reason=str(parsed.get("reason", "")),
    )

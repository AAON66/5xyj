from __future__ import annotations

import json

import pytest

from backend.app.core.config import Settings
from backend.app.parsers import HeaderColumn, extract_header_structure
from backend.app.services import (
    map_header_with_llm,
    normalize_header_column,
    normalize_header_column_with_fallback,
    normalize_header_extraction_with_fallback,
)
import backend.app.services.header_normalizer as header_normalizer_module
import backend.app.services.llm_mapping_service as llm_mapping_module


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise llm_mapping_module.httpx.HTTPStatusError(
                "error",
                request=llm_mapping_module.httpx.Request("POST", "https://api.deepseek.test/chat/completions"),
                response=llm_mapping_module.httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


class DummyAsyncClient:
    def __init__(self, response_payload: dict | None = None, status_code: int = 200, error: Exception | None = None, **_: object):
        self.response_payload = response_payload
        self.status_code = status_code
        self.error = error
        self.calls: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, *, headers: dict, json: dict):
        self.calls.append({"url": url, "headers": headers, "json": json})
        if self.error is not None:
            raise self.error
        return DummyResponse(self.response_payload or {}, status_code=self.status_code)


@pytest.mark.anyio
async def test_rule_match_does_not_call_llm(monkeypatch) -> None:
    called = {"value": False}

    async def fake_llm(*args, **kwargs):
        called["value"] = True
        raise AssertionError("LLM should not be called when rule mapping succeeds.")

    monkeypatch.setattr(header_normalizer_module, "map_header_with_llm", fake_llm)
    column = HeaderColumn(2, "B", ["姓名"], "姓名")

    decision = await normalize_header_column_with_fallback(column, region="guangzhou")

    assert decision.canonical_field == "person_name"
    assert decision.mapping_source == "rule"
    assert called["value"] is False


@pytest.mark.anyio
async def test_llm_service_skips_when_api_key_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="", enable_llm_fallback=True),
    )

    result = await map_header_with_llm("未知字段 / 金额", region="guangzhou")

    assert result.status == "skipped_no_api_key"
    assert result.canonical_field is None
    assert result.candidate_fields == []


@pytest.mark.anyio
async def test_llm_fallback_applies_high_confidence_mapping(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "canonical_field": "company_total_amount",
                            "confidence": 0.93,
                            "candidate_fields": ["company_total_amount", "total_amount"],
                            "reason": "matched semantic total company amount",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }
    client = DummyAsyncClient(response_payload=payload)

    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="test-key", deepseek_api_base_url="https://api.deepseek.test", enable_llm_fallback=True),
    )
    monkeypatch.setattr(llm_mapping_module.httpx, "AsyncClient", lambda **kwargs: client)

    column = HeaderColumn(6, "F", ["神秘单位金额"], "神秘单位金额")
    decision = await normalize_header_column_with_fallback(column, region="guangzhou", confidence_threshold=0.8)

    assert decision.canonical_field == "company_total_amount"
    assert decision.mapping_source == "llm"
    assert decision.llm_attempted is True
    assert decision.llm_status == "success"
    assert decision.candidate_fields == ["company_total_amount", "total_amount"]
    assert client.calls[0]["url"] == "/chat/completions"


@pytest.mark.anyio
async def test_llm_fallback_does_not_accept_low_confidence_result(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "canonical_field": "total_amount",
                            "confidence": 0.42,
                            "candidate_fields": ["total_amount", "company_total_amount"],
                            "reason": "low confidence guess",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }
    client = DummyAsyncClient(response_payload=payload)

    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="test-key", deepseek_api_base_url="https://api.deepseek.test", enable_llm_fallback=True),
    )
    monkeypatch.setattr(llm_mapping_module.httpx, "AsyncClient", lambda **kwargs: client)

    column = HeaderColumn(7, "G", ["模糊金额列"], "模糊金额列")
    decision = await normalize_header_column_with_fallback(column, region="guangzhou", confidence_threshold=0.8)

    assert decision.canonical_field is None
    assert decision.mapping_source == "unmapped"
    assert decision.llm_attempted is True
    assert decision.llm_status == "success"
    assert decision.candidate_fields == ["total_amount", "company_total_amount"]


@pytest.mark.anyio
async def test_llm_fallback_handles_http_error(monkeypatch) -> None:
    client = DummyAsyncClient(error=llm_mapping_module.httpx.ConnectError("network down"))

    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="test-key", deepseek_api_base_url="https://api.deepseek.test", enable_llm_fallback=True),
    )
    monkeypatch.setattr(llm_mapping_module.httpx, "AsyncClient", lambda **kwargs: client)

    column = HeaderColumn(8, "H", ["异常列"], "异常列")
    decision = await normalize_header_column_with_fallback(column, region="guangzhou")

    assert decision.canonical_field is None
    assert decision.mapping_source == "unmapped"
    assert decision.llm_attempted is True
    assert decision.llm_status == "error"


@pytest.mark.anyio
async def test_normalize_header_extraction_with_fallback_preserves_rule_and_unmapped_columns(monkeypatch) -> None:
    async def fake_llm(signature: str, region: str | None = None):
        if signature == "神秘单位金额":
            return llm_mapping_module.LLMMappingResult(
                raw_header_signature=signature,
                canonical_field="company_total_amount",
                confidence=0.91,
                candidate_fields=["company_total_amount", "total_amount"],
                status="success",
                reason="ok",
            )
        return llm_mapping_module.LLMMappingResult(
            raw_header_signature=signature,
            canonical_field=None,
            confidence=None,
            candidate_fields=[],
            status="skipped_no_api_key",
            reason="no key",
        )

    monkeypatch.setattr(header_normalizer_module, "map_header_with_llm", fake_llm)
    extraction = extract_header_structure(next(p for p in sorted((header_normalizer_module.Path(__file__).resolve().parents[2] / 'data' / 'samples').glob('*.xlsx')) if '广分' in p.name))
    extraction.columns = [
        extraction.columns[1],
        HeaderColumn(99, "CU", ["神秘单位金额"], "神秘单位金额"),
    ]

    result = await normalize_header_extraction_with_fallback(extraction, region="guangzhou")
    decisions = {decision.raw_header_signature: decision for decision in result.decisions}

    assert decisions["姓名"].canonical_field == "person_name"
    assert decisions["姓名"].mapping_source == "rule"
    assert decisions["神秘单位金额"].canonical_field == "company_total_amount"
    assert decisions["神秘单位金额"].mapping_source == "llm"

@pytest.mark.anyio
async def test_llm_service_respects_disabled_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="test-key", enable_llm_fallback=False),
    )

    result = await map_header_with_llm("???? / ??", region="guangzhou")

    assert result.status == "disabled"
    assert result.canonical_field is None
    assert result.candidate_fields == []


@pytest.mark.anyio
async def test_llm_service_returns_invalid_response_when_payload_is_not_json(monkeypatch) -> None:
    payload = {"choices": [{"message": {"content": "not-json"}}]}
    client = DummyAsyncClient(response_payload=payload)

    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="test-key", deepseek_api_base_url="https://api.deepseek.test", enable_llm_fallback=True),
    )
    monkeypatch.setattr(llm_mapping_module.httpx, "AsyncClient", lambda **kwargs: client)

    result = await map_header_with_llm("???? / ??", region="guangzhou")

    assert result.status == "invalid_response"
    assert result.canonical_field is None
    assert result.candidate_fields == []


@pytest.mark.anyio
async def test_llm_service_filters_invalid_candidates_and_preserves_model_and_auth(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "canonical_field": "company_total_amount",
                            "confidence": 0.88,
                            "candidate_fields": ["company_total_amount", "not_a_field", "total_amount"],
                            "reason": "valid canonical with noisy candidates",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }
    client = DummyAsyncClient(response_payload=payload)

    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(
            deepseek_api_key="integration-key",
            deepseek_api_base_url="https://api.deepseek.test/v1",
            deepseek_model="deepseek-reasoner",
            enable_llm_fallback=True,
        ),
    )
    monkeypatch.setattr(llm_mapping_module.httpx, "AsyncClient", lambda **kwargs: client)

    result = await map_header_with_llm("??????", region="guangzhou")

    assert result.status == "success"
    assert result.canonical_field == "company_total_amount"
    assert result.candidate_fields == ["company_total_amount", "total_amount"]
    assert client.calls[0]["headers"]["Authorization"] == "Bearer integration-key"
    assert client.calls[0]["json"]["model"] == "deepseek-reasoner"
    assert client.calls[0]["json"]["response_format"] == {"type": "json_object"}
    assert client.calls[0]["json"]["messages"][1]["content"]


@pytest.mark.anyio
async def test_llm_service_keeps_unmapped_when_canonical_field_is_invalid(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "canonical_field": "unknown_field",
                            "confidence": 0.97,
                            "candidate_fields": ["unknown_field", "total_amount"],
                            "reason": "bad canonical field",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }
    client = DummyAsyncClient(response_payload=payload)

    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="test-key", deepseek_api_base_url="https://api.deepseek.test", enable_llm_fallback=True),
    )
    monkeypatch.setattr(llm_mapping_module.httpx, "AsyncClient", lambda **kwargs: client)

    column = HeaderColumn(11, "K", ["?????"], "?????")
    decision = await normalize_header_column_with_fallback(column, region="guangzhou", confidence_threshold=0.8)

    assert decision.canonical_field is None
    assert decision.mapping_source == "unmapped"
    assert decision.llm_attempted is True
    assert decision.llm_status == "success"
    assert decision.candidate_fields == ["total_amount"]

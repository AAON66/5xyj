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


class DummyClient:
    def __init__(self, response_payload: dict | None = None, status_code: int = 200, error: Exception | None = None, **_: object):
        self.response_payload = response_payload
        self.status_code = status_code
        self.error = error
        self.calls: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url: str, *, headers: dict, json: dict):
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

    column = HeaderColumn(8, "H", ["未知金额字段"], "未知金额字段")
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

    column = HeaderColumn(11, "K", ["神秘单位金额"], "神秘单位金额")
    decision = await normalize_header_column_with_fallback(column, region="guangzhou", confidence_threshold=0.8)

    assert decision.canonical_field is None
    assert decision.mapping_source == "unmapped"
    assert decision.llm_attempted is True
    assert decision.llm_status == "success"
    assert decision.candidate_fields == ["total_amount"]


def test_sync_llm_fallback_accepts_fenced_json_response(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": "```json\n" + json.dumps(
                        {
                            "canonical_field": "company_total_amount",
                            "confidence": 0.91,
                            "candidate_fields": ["company_total_amount", "total_amount"],
                            "reason": "fenced json response",
                        },
                        ensure_ascii=False,
                    ) + "\n```"
                }
            }
        ]
    }
    client = DummyClient(response_payload=payload)

    monkeypatch.setattr(
        llm_mapping_module,
        "get_settings",
        lambda: Settings(deepseek_api_key="sync-key", deepseek_api_base_url="https://api.deepseek.test", enable_llm_fallback=True),
    )
    monkeypatch.setattr(llm_mapping_module.httpx, "Client", lambda **kwargs: client)

    result = llm_mapping_module.map_header_with_llm_sync("??????", region="guangzhou")

    assert result.status == "success"
    assert result.canonical_field == "company_total_amount"
    assert result.candidate_fields == ["company_total_amount", "total_amount"]
    assert client.calls[0]["url"] == "/chat/completions"



@pytest.mark.anyio
async def test_llm_service_accepts_textual_high_confidence(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "canonical_field": "company_total_amount",
                            "confidence": "high",
                            "candidate_fields": ["company_total_amount", "total_amount"],
                            "reason": "text confidence from model",
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

    result = await map_header_with_llm("mystery company amount", region="guangzhou")

    assert result.status == "success"
    assert result.canonical_field == "company_total_amount"
    assert result.confidence == pytest.approx(0.92)


@pytest.mark.anyio
async def test_llm_service_accepts_percentage_confidence(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "canonical_field": "total_amount",
                            "confidence": "87%",
                            "candidate_fields": ["total_amount"],
                            "reason": "percentage confidence from model",
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

    result = await map_header_with_llm("mystery total", region="guangzhou")

    assert result.status == "success"
    assert result.confidence == pytest.approx(0.87)


@pytest.mark.anyio
async def test_llm_service_tolerates_unparseable_confidence(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "canonical_field": "total_amount",
                            "confidence": "uncertain",
                            "candidate_fields": ["total_amount"],
                            "reason": "unparseable confidence",
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

    result = await map_header_with_llm("mystery total", region="guangzhou")

    assert result.status == "success"
    assert result.confidence is None


def test_sync_fallback_skips_irrelevant_third_party_columns(monkeypatch) -> None:
    def fail_llm(*args, **kwargs):
        raise AssertionError("LLM should not be called for irrelevant helper columns.")

    monkeypatch.setattr(header_normalizer_module, "map_header_with_llm_sync", fail_llm)
    column = HeaderColumn(12, "L", ["养老企业基数"], "养老企业基数")

    decision = header_normalizer_module.normalize_header_column_with_sync_fallback(column, region="shenzhen")

    assert decision.canonical_field is None
    assert decision.mapping_source == "unmapped"
    assert decision.llm_attempted is False
    assert decision.llm_status == "skipped_irrelevant"


def test_rule_mapping_covers_third_party_merge_headers() -> None:
    columns = [
        HeaderColumn(1, "A", ["客户名称"], "客户名称"),
        HeaderColumn(2, "B", ["身份证号"], "身份证号"),
        HeaderColumn(3, "C", ["参保地"], "参保地"),
        HeaderColumn(4, "D", ["账单年月"], "账单年月"),
        HeaderColumn(5, "E", ["养老企业汇缴"], "养老企业汇缴"),
        HeaderColumn(6, "F", ["社保合计"], "社保合计"),
        HeaderColumn(7, "G", ["公积金企业汇缴"], "公积金企业汇缴"),
        HeaderColumn(8, "H", ["公积金合计"], "公积金合计"),
    ]

    decisions = {
        column.signature: normalize_header_column(column, region="shenzhen")
        for column in columns
    }

    assert decisions["客户名称"].canonical_field == "company_name"
    assert decisions["身份证号"].canonical_field == "id_number"
    assert decisions["参保地"].canonical_field == "region"
    assert decisions["账单年月"].canonical_field == "billing_period"
    assert decisions["养老企业汇缴"].canonical_field == "pension_company"
    assert decisions["社保合计"].canonical_field == "total_amount"
    assert decisions["公积金企业汇缴"].canonical_field == "housing_fund_company"
    assert decisions["公积金合计"].canonical_field == "housing_fund_total"

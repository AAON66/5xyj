from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.core.config import ROOT_DIR, Settings
import backend.app.services.region_detection_service as region_module


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise region_module.httpx.HTTPStatusError(
                'error',
                request=region_module.httpx.Request('POST', 'https://api.deepseek.test/chat/completions'),
                response=region_module.httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


class DummyClient:
    def __init__(self, response_payload: dict | None = None, status_code: int = 200, error: Exception | None = None, **_: object):
        self.response_payload = response_payload
        self.status_code = status_code
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url: str, *, headers: dict, json: dict):
        if self.error is not None:
            raise self.error
        return DummyResponse(self.response_payload or {}, status_code=self.status_code)

SAMPLES_DIR = ROOT_DIR / 'data' / 'samples'


def find_sample(keyword: str) -> Path:
    for path in sorted(SAMPLES_DIR.glob('*.xlsx')):
        if keyword in path.name:
            return path
    pytest.skip(f'Sample containing {keyword!r} was not found in {SAMPLES_DIR}.')


def test_detect_region_for_workbook_uses_workbook_clues_for_guangzhou() -> None:
    sample_path = find_sample('\u5e7f\u5206')

    result = region_module.detect_region_for_workbook(sample_path, filename='generic.xlsx')

    assert result.region == 'guangzhou'
    assert result.source == 'rule'
    assert result.confidence >= 0.5


def test_detect_region_for_workbook_uses_workbook_clues_for_xiamen() -> None:
    sample_path = find_sample('\u53a6\u95e8202602')

    result = region_module.detect_region_for_workbook(sample_path, filename='generic.xlsx')

    assert result.region == 'xiamen'
    assert result.source == 'rule'
    assert result.confidence >= 0.5


def test_merge_region_detection_prefers_combined_rule_and_llm_when_they_agree() -> None:
    local = region_module.RegionDetectionResult(
        region='shenzhen',
        confidence=0.72,
        source='rule',
        reason='local workbook clues',
        local_confidence=0.72,
    )
    llm = region_module.LLMRegionResult(
        region='shenzhen',
        confidence=0.92,
        candidate_regions=['shenzhen', 'guangzhou'],
        status='success',
        reason='header semantics point to shenzhen',
    )

    result = region_module.merge_region_detection_results(local, llm)

    assert result.region == 'shenzhen'
    assert result.source == 'llm+rule'
    assert result.confidence >= 0.9


def test_merge_region_detection_prefers_llm_when_local_is_missing() -> None:
    local = region_module.RegionDetectionResult(
        region=None,
        confidence=0.0,
        source='rule',
        reason='no local signals',
        local_confidence=0.0,
    )
    llm = region_module.LLMRegionResult(
        region='wuhan',
        confidence=0.89,
        candidate_regions=['wuhan', 'changsha'],
        status='success',
        reason='workbook title and repeated unit/personal structure match wuhan',
    )

    result = region_module.merge_region_detection_results(local, llm)

    assert result.region == 'wuhan'
    assert result.source == 'llm'
    assert result.confidence == pytest.approx(0.89)



def test_detect_region_with_llm_sync_accepts_textual_high_confidence(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": '{"region": "shenzhen", "confidence": "high", "candidate_regions": ["shenzhen"], "reason": "text confidence"}'
                }
            }
        ]
    }
    workbook_context = region_module.WorkbookRegionContext(
        filename='generic.xlsx',
        source_kind='social_security',
        sheet_names=['????'],
        sample_text='?? ????',
    )

    monkeypatch.setattr(
        region_module,
        'get_settings',
        lambda: Settings(deepseek_api_key='test-key', deepseek_api_base_url='https://api.deepseek.test', enable_llm_fallback=True),
    )
    monkeypatch.setattr(region_module.httpx, 'Client', lambda **kwargs: DummyClient(response_payload=payload))

    result = region_module.detect_region_with_llm_sync(workbook_context)

    assert result.status == 'success'
    assert result.region == 'shenzhen'
    assert result.confidence == pytest.approx(0.92)



def test_detect_region_with_llm_sync_accepts_percentage_confidence(monkeypatch) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": '{"region": "xiamen", "confidence": "88%", "candidate_regions": ["xiamen"], "reason": "percentage confidence"}'
                }
            }
        ]
    }
    workbook_context = region_module.WorkbookRegionContext(
        filename='generic.xlsx',
        source_kind='housing_fund',
        sheet_names=['???????????'],
        sample_text='?? ???? ????',
    )

    monkeypatch.setattr(
        region_module,
        'get_settings',
        lambda: Settings(deepseek_api_key='test-key', deepseek_api_base_url='https://api.deepseek.test', enable_llm_fallback=True),
    )
    monkeypatch.setattr(region_module.httpx, 'Client', lambda **kwargs: DummyClient(response_payload=payload))

    result = region_module.detect_region_with_llm_sync(workbook_context)

    assert result.status == 'success'
    assert result.region == 'xiamen'
    assert result.confidence == pytest.approx(0.88)

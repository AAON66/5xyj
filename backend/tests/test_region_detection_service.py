from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.core.config import ROOT_DIR
import backend.app.services.region_detection_service as region_module

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

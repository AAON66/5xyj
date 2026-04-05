from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from backend.app.mappings.regions import REGION_LABELS

DATE_PATTERN = re.compile(r'(20\d{2}\u5e74\d{1,2}\u6708|20\d{4}|\d{6})')
FILENAME_NOISE = (
    '\u793e\u4f1a\u4fdd\u9669\u8d39\u7533\u62a5\u4e2a\u4eba\u660e\u7ec6\u8868',
    '\u793e\u4fdd\u7f34\u8d39\u660e\u7ec6',
    '\u793e\u4fdd\u660e\u7ec6',
    '\u793e\u4fdd\u8d26\u5355',
    '\u793e\u4fdd\u53f0\u8d26',
    '\u516c\u79ef\u91d1\u8d26\u5355',
    '\u516c\u79ef\u91d1\u6c47\u7f34\u660e\u7ec6',
    '\u516c\u79ef\u91d1',
    '\u4f4f\u623f\u516c\u79ef\u91d1\u5355\u4f4d\u6c47\u7f34\u660e\u7ec6',
    '\u5355\u7b14\u7f34\u5b58\u6e05\u5355',
    '\u8d26\u5355',
    '\u660e\u7ec6',
    '\u53f0\u8d26',
    '\u8865\u7f34',
)


def infer_company_name_from_filename(filename: str, region: Optional[str]) -> Optional[str]:
    stem = Path(filename).stem
    if '--' in stem:
        tail = stem.split('--')[-1].strip()
        return tail or None

    cleaned = DATE_PATTERN.sub('', stem)
    cleaned = cleaned.replace('\u8865\u7f341\u6708\u5165\u804c2\u4eba', '')
    for noise in FILENAME_NOISE:
        cleaned = cleaned.replace(noise, '')
    if region:
        cleaned = cleaned.replace(REGION_LABELS.get(region, ''), '')
    cleaned = re.sub(r'[()\uff08\uff09_\-\s]+', '', cleaned)
    return cleaned or (REGION_LABELS.get(region) if region else None)

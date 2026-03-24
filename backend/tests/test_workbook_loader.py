from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from backend.app.parsers.workbook_loader import load_workbook_compatible


APP_DB = Path(__file__).resolve().parents[2] / 'data' / 'app.db'


def find_uploaded_sample(filename: str) -> Path:
    if not APP_DB.exists():
        pytest.skip(f'Application database was not found at {APP_DB}.')

    connection = sqlite3.connect(APP_DB)
    try:
        row = connection.execute(
            'select file_path from source_files where file_name = ? order by uploaded_at desc limit 1',
            (filename,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        pytest.skip(f'Uploaded sample {filename!r} was not found in {APP_DB}.')

    sample_path = Path(row[0])
    if not sample_path.exists():
        pytest.skip(f'Uploaded sample path no longer exists: {sample_path}.')
    return sample_path


def test_load_workbook_compatible_supports_legacy_xls() -> None:
    sample_path = find_uploaded_sample('广州裂变202601社保账单.xls')

    workbook = load_workbook_compatible(sample_path, read_only=True, data_only=True)
    try:
        assert workbook.sheetnames == ['sheet1']
        sheet = workbook[workbook.sheetnames[0]]
        assert sheet.max_row > 10
        assert any(sheet.cell(row=7, column=column).value for column in range(1, min(sheet.max_column, 12) + 1))
    finally:
        workbook.close()


def test_load_workbook_compatible_falls_back_for_disguised_xls_content() -> None:
    sample_path = find_uploaded_sample('厦门公积金202601公积金账单.xlsx')

    workbook = load_workbook_compatible(sample_path, read_only=True, data_only=True)
    try:
        assert workbook.sheetnames == ['汇缴明细查询个人']
        sheet = workbook[workbook.sheetnames[0]]
        assert sheet.max_row > 5
        assert any(sheet.cell(row=1, column=column).value for column in range(1, min(sheet.max_column, 12) + 1))
    finally:
        workbook.close()

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.models import Base
from backend.app.models.sync_config import SyncConfig
from backend.app.services.fusion_input_service import (
    build_burden_key,
    load_burden_rows_from_feishu,
    parse_burden_workbook,
)


def make_burden_workbook(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def build_test_db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_build_burden_key_prefers_employee_id() -> None:
    assert build_burden_key("E9001", "440101199001010011") == ("E9001", "")
    assert build_burden_key(None, "440101199001010011") == ("", "440101199001010011")
    assert build_burden_key("  ", "  ") is None


def test_parse_burden_workbook_supports_aliases_and_skips_bad_rows() -> None:
    workbook_bytes = make_burden_workbook(
        [
            ["员工工号", "证件号码", "社保个人承担额", "公积金个人承担额"],
            ["E1001", "440101199001010001", "11.10", "22.20"],
            [None, None, "33.30", "44.40"],
            ["E1001", "440101199001010001", "55.50", "66.60"],
            ["E1002", "440101199001010002", "77.70", None],
        ]
    )

    rows, diagnostics = parse_burden_workbook(workbook_bytes, "burden.xlsx")

    assert len(rows) == 1
    assert rows[0].employee_id == "E1002"
    assert rows[0].personal_social_burden == rows[0].personal_social_burden.__class__("77.70")
    assert diagnostics.missing_key_rows == 1
    assert diagnostics.duplicate_key_rows == 2
    assert diagnostics.unmatched_rows == 0


class FakeFeishuClient:
    def __init__(self):
        self.calls: list[tuple[str, str, str | None]] = []

    async def search_records(self, app_token: str, table_id: str, filter_expr: str | None = None, page_token: str | None = None, page_size: int = 500):
        self.calls.append((app_token, table_id, page_token))
        return {
            "data": {
                "items": [
                    {
                        "fields": {
                            "员工工号列": "E2001",
                            "社保承担列": 88.5,
                            "公积金承担列": 16,
                            "姓名列": "不应用于主键",
                        }
                    },
                    {
                        "fields": {
                            "身份证列": "440101199001010099",
                            "社保承担列": 12,
                        }
                    },
                    {
                        "fields": {
                            "员工工号列": "E2001",
                            "社保承担列": 99,
                        }
                    },
                ],
                "has_more": False,
            }
        }


def test_load_burden_rows_from_feishu_uses_whitelisted_mapping_and_diagnostics() -> None:
    db = build_test_db()
    config = SyncConfig(
        name="burden-config",
        app_token="app-token",
        table_id="tbl-001",
        granularity="detail",
        field_mapping={
            "员工工号列": "employee_id",
            "身份证列": "id_number",
            "社保承担列": "personal_social_burden",
            "公积金承担列": "personal_housing_burden",
            "姓名列": "person_name",
        },
        is_active=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    client = FakeFeishuClient()
    rows, diagnostics = __import__("asyncio").run(load_burden_rows_from_feishu(db, client, config.id))

    assert client.calls == [("app-token", "tbl-001", None)]
    assert len(rows) == 1
    assert rows[0].employee_id is None
    assert rows[0].id_number == "440101199001010099"
    assert rows[0].personal_social_burden == rows[0].personal_social_burden.__class__("12")
    assert diagnostics.duplicate_key_rows == 2
    assert diagnostics.missing_key_rows == 0
    assert diagnostics.unmatched_rows == 0

from __future__ import annotations

import shutil
import time
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import UploadFile

from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.models import Base
import backend.app.services.aggregate_service as aggregate_service_module

ARTIFACTS_ROOT = ROOT_DIR / '.test_artifacts' / 'aggregate_service'


def build_runtime(test_name: str):
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    settings = Settings(
        app_name='aggregate-service-test',
        app_version='0.2.0',
        database_url=f"sqlite:///{(artifacts_dir / 'aggregate.db').as_posix()}",
        upload_dir=str(artifacts_dir / 'uploads'),
        samples_dir=str(artifacts_dir / 'samples'),
        templates_dir=str(artifacts_dir / 'templates'),
        outputs_dir=str(artifacts_dir / 'outputs'),
        log_format='plain',
    )
    engine = create_database_engine(settings)
    session_factory = create_session_factory(settings)
    Base.metadata.create_all(engine)
    return settings, session_factory


@pytest.mark.anyio
async def test_run_simple_aggregate_emits_parse_heartbeat_and_fine_grained_messages(monkeypatch) -> None:
    settings, session_factory = build_runtime('parse_progress_heartbeat')
    db = session_factory()
    events: list[dict[str, object]] = []

    batch = SimpleNamespace(id='batch-1', batch_name='batch-1', source_files=[SimpleNamespace()])

    async def fake_create_import_batch(*args, **kwargs):
        return batch

    def fake_parse_import_batch(worker_db, batch_id: str, progress_callback=None):
        base_payload = {
            'current': 1,
            'file_index': 1,
            'total': 1,
            'file_name': '长沙202602公积金账单.xlsx',
            'batch_id': batch_id,
            'batch_name': 'batch-1',
            'source_file_id': 'sf-1',
            'source_kind': 'housing_fund',
            'region': 'changsha',
            'company_name': '李猛社保',
            'worker_count': 2,
        }
        progress_callback({**base_payload, 'phase': 'parse_queued'})
        progress_callback({**base_payload, 'phase': 'parse_started'})
        time.sleep(0.08)
        progress_callback(
            {
                **base_payload,
                'phase': 'parse_analyzed',
                'normalized_record_count': 47,
                'filtered_row_count': 0,
                'unmapped_header_count': 1,
            }
        )
        time.sleep(0.02)
        progress_callback(
            {
                **base_payload,
                'phase': 'parse_saved',
                'normalized_record_count': 47,
                'filtered_row_count': 0,
                'unmapped_header_count': 1,
                'raw_sheet_name': 'Sheet4',
            }
        )
        return SimpleNamespace(
            source_files=[
                SimpleNamespace(
                    source_file_id='sf-1',
                    file_name='长沙202602公积金账单.xlsx',
                    source_kind='housing_fund',
                    region='changsha',
                    company_name='李猛社保',
                    normalized_record_count=47,
                    filtered_row_count=0,
                )
            ]
        )

    monkeypatch.setattr(aggregate_service_module, 'create_import_batch', fake_create_import_batch)
    monkeypatch.setattr(aggregate_service_module, 'parse_import_batch', fake_parse_import_batch)
    monkeypatch.setattr(
        aggregate_service_module,
        'validate_batch',
        lambda db, batch_id: SimpleNamespace(total_issue_count=0),
    )
    monkeypatch.setattr(
        aggregate_service_module,
        '_match_for_simple_aggregate',
        lambda db, batch_id, **kwargs: SimpleNamespace(
            blocked_reason=None,
            matched_count=0,
            unmatched_count=0,
            duplicate_count=0,
            low_confidence_count=0,
        ),
    )
    monkeypatch.setattr(
        aggregate_service_module,
        'export_batch',
        lambda db, batch_id, settings: SimpleNamespace(
            status='exported',
            export_status='completed',
            artifacts=[
                SimpleNamespace(template_type='salary', status='completed', file_path='salary.xlsx', error_message=None, row_count=1),
                SimpleNamespace(template_type='final_tool', status='completed', file_path='tool.xlsx', error_message=None, row_count=1),
            ],
        ),
    )
    monkeypatch.setattr(aggregate_service_module, 'PARSE_PROGRESS_HEARTBEAT_SECONDS', 0.02)
    monkeypatch.setattr(aggregate_service_module, 'PARSE_PROGRESS_POLL_INTERVAL_SECONDS', 0.005)

    async def progress(payload: dict[str, object]) -> None:
        events.append(payload)

    try:
        upload = UploadFile(filename='dummy.xlsx', file=BytesIO(b'dummy'))
        result = await aggregate_service_module.run_simple_aggregate(
            db,
            settings,
            files=[upload],
            progress_callback=progress,
        )
    finally:
        db.close()

    parse_messages = [str(event['message']) for event in events if event.get('stage') == 'parse']
    parse_events = [event for event in events if event.get('stage') == 'parse']

    assert result.export_status == 'completed'
    assert any('加入解析队列' in message for message in parse_messages)
    assert any('正在解析公积金文件' in message for message in parse_messages)
    assert any('识别分析' in message for message in parse_messages)
    assert any('结果保存' in message for message in parse_messages)
    assert any(event.get('parse_summary', {}).get('worker_count') == 2 for event in parse_events)
    assert any(event.get('parse_summary', {}).get('saved_count') == 1 for event in parse_events)
    assert any(event.get('parse_files') and event['parse_files'][0].get('raw_sheet_name') == 'Sheet4' for event in parse_events)

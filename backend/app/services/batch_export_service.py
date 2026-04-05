from __future__ import annotations

from typing import Optional

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.exporters import export_dual_templates
from backend.app.models import ExportArtifact, ExportJob
from backend.app.models.enums import BatchStatus, TemplateType
from backend.app.schemas.imports import BatchExportRead, ExportArtifactRead
from backend.app.services.import_service import get_import_batch

BLOCKED_REASON_NOT_MATCHED = 'Batch must complete matching before export can run.'
BLOCKED_REASON_MATCH_BLOCKED = 'Batch export is blocked because employee matching is blocked.'
NO_EXPORT_JOB_REASON = 'Export has not been requested yet.'
AUTO_BATCH_NAME_PREFIX = 'import-batch-'
MAX_EXPORT_PREFIX_LENGTH = 32
INVALID_EXPORT_FILENAME_CHARS_RE = re.compile(r'[\\/:*?"<>|]+')
EXPORT_PREFIX_SPACING_RE = re.compile(r'[\s_]+')


class ExportBlockedError(Exception):
    """Raised when a batch cannot be exported yet."""


@dataclass
class ExportExecutionResult:
    job: ExportJob
    artifacts: list[ExportArtifactRead]


def export_batch(db: Session, batch_id: str, settings: Settings) -> BatchExportRead:
    batch = get_import_batch(db, batch_id)
    _ensure_exportable(batch)
    export_started_at = datetime.now().astimezone()

    job = ExportJob(batch_id=batch.id, status='pending')
    db.add(job)
    db.flush()

    output_dir = settings.outputs_path / batch.id / job.id
    output_dir.mkdir(parents=True, exist_ok=True)

    result = export_dual_templates(
        batch.normalized_records,
        output_dir=output_dir,
        salary_template_path=settings.salary_template_file,
        final_tool_template_path=settings.final_tool_template_file,
        export_prefix=_build_export_prefix(batch, exported_at=export_started_at),
        settings=settings,
    )

    artifact_models: list[ExportArtifact] = []
    artifact_reads: list[ExportArtifactRead] = []
    for artifact in result.artifacts:
        template_type = TemplateType(artifact.template_type)
        model = ExportArtifact(
            export_job_id=job.id,
            template_type=template_type,
            file_path=artifact.file_path,
            status=artifact.status,
            error_message=artifact.error_message,
        )
        artifact_models.append(model)
        artifact_reads.append(
            ExportArtifactRead(
                template_type=artifact.template_type,
                status=artifact.status,
                file_path=artifact.file_path,
                error_message=artifact.error_message,
                row_count=artifact.row_count,
            )
        )
    db.add_all(artifact_models)

    job.status = result.status
    job.completed_at = datetime.now(timezone.utc)
    batch.status = BatchStatus.EXPORTED if result.status == 'completed' else BatchStatus.FAILED
    db.commit()
    db.refresh(job)
    db.refresh(batch)

    return BatchExportRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        export_job_id=job.id,
        export_status=job.status,
        blocked_reason=None,
        artifacts=artifact_reads,
        completed_at=job.completed_at,
    )


def get_batch_export(db: Session, batch_id: str) -> BatchExportRead:
    batch = get_import_batch(db, batch_id)
    if not batch.export_jobs:
        return BatchExportRead(
            batch_id=batch.id,
            batch_name=batch.batch_name,
            status=batch.status.value,
            export_job_id=None,
            export_status=None,
            blocked_reason=_derive_non_export_reason(batch),
            artifacts=[],
            completed_at=None,
        )

    latest_job = max(
        batch.export_jobs,
        key=lambda item: (item.completed_at or item.created_at or datetime.min.replace(tzinfo=timezone.utc), item.created_at),
    )
    return BatchExportRead(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        export_job_id=latest_job.id,
        export_status=latest_job.status,
        blocked_reason=None,
        artifacts=[
            ExportArtifactRead(
                template_type=artifact.template_type.value,
                status=artifact.status,
                file_path=artifact.file_path,
                error_message=artifact.error_message,
                row_count=len(batch.normalized_records) if artifact.status == 'completed' else 0,
            )
            for artifact in sorted(latest_job.artifacts, key=lambda item: item.template_type.value)
        ],
        completed_at=latest_job.completed_at,
    )


def _ensure_exportable(batch) -> None:
    if batch.status == BatchStatus.BLOCKED:
        raise ExportBlockedError(BLOCKED_REASON_MATCH_BLOCKED)
    if not batch.match_results:
        raise ExportBlockedError(BLOCKED_REASON_NOT_MATCHED)



def _derive_non_export_reason(batch) -> Optional[str]:
    if batch.status == BatchStatus.BLOCKED:
        return BLOCKED_REASON_MATCH_BLOCKED
    if not batch.match_results:
        return BLOCKED_REASON_NOT_MATCHED
    return NO_EXPORT_JOB_REASON


def _build_export_prefix(batch, *, exported_at: Optional[datetime] = None) -> str:
    timestamp_source = exported_at or datetime.now().astimezone()
    timestamp_prefix = timestamp_source.strftime('%Y%m%d-%H%M%S')
    raw_batch_name = (batch.batch_name or '').strip()
    if not raw_batch_name or raw_batch_name.startswith(AUTO_BATCH_NAME_PREFIX):
        return timestamp_prefix

    cleaned = INVALID_EXPORT_FILENAME_CHARS_RE.sub(' ', raw_batch_name)
    cleaned = EXPORT_PREFIX_SPACING_RE.sub('_', cleaned).strip(' ._')
    if not cleaned:
        return timestamp_prefix
    if len(cleaned) > MAX_EXPORT_PREFIX_LENGTH:
        cleaned = cleaned[:MAX_EXPORT_PREFIX_LENGTH].rstrip(' ._')
    return cleaned or timestamp_prefix

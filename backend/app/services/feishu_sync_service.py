"""Feishu Bitable push/pull sync service with conflict detection and provenance tracking."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from itertools import islice
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.normalized_record import NormalizedRecord
from backend.app.models.sync_config import SyncConfig
from backend.app.models.sync_job import SyncJob
from backend.app.schemas.feishu import ConflictPreview, ConflictRecord
from backend.app.services.feishu_client import FeishuClient


# Amount fields on NormalizedRecord that are Decimal type
AMOUNT_FIELDS = [
    "payment_base", "payment_salary", "total_amount",
    "company_total_amount", "personal_total_amount",
    "pension_company", "pension_personal",
    "medical_company", "medical_personal",
    "medical_maternity_company", "maternity_amount",
    "unemployment_company", "unemployment_personal",
    "injury_company",
    "supplementary_medical_company", "supplementary_pension_company",
    "large_medical_personal",
    "housing_fund_base", "housing_fund_personal", "housing_fund_company", "housing_fund_total",
    "late_fee", "interest",
]


def _chunked(iterable: list, size: int):
    """Yield successive chunks of the given size from iterable."""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


def _record_to_feishu_row(record: NormalizedRecord, field_mapping: dict[str, str]) -> dict[str, Any]:
    """Transform a NormalizedRecord to a Feishu row dict using field_mapping.

    field_mapping: {feishu_column_name: system_field_name}
    Decimal values are converted to float for JSON serialization.
    """
    row: dict[str, Any] = {}
    for feishu_col, sys_field in field_mapping.items():
        value = getattr(record, sys_field, None)
        if isinstance(value, Decimal):
            value = float(value)
        row[feishu_col] = value
    return row


def _summarize_records(
    records: list[NormalizedRecord],
    field_mapping: dict[str, str],
) -> list[dict[str, Any]]:
    """Group records by company_name+region+billing_period and sum amount fields."""
    groups: dict[tuple, dict[str, Any]] = {}
    # Determine which mapped system fields are amount fields
    amount_sys_fields = set(AMOUNT_FIELDS)

    for record in records:
        key = (record.company_name, record.region, record.billing_period)
        if key not in groups:
            groups[key] = {}
            for feishu_col, sys_field in field_mapping.items():
                value = getattr(record, sys_field, None)
                if sys_field in amount_sys_fields:
                    groups[key][feishu_col] = float(value) if isinstance(value, Decimal) and value is not None else (value or 0)
                else:
                    groups[key][feishu_col] = value
        else:
            for feishu_col, sys_field in field_mapping.items():
                if sys_field in amount_sys_fields:
                    value = getattr(record, sys_field, None)
                    add = float(value) if isinstance(value, Decimal) and value is not None else 0
                    existing = groups[key].get(feishu_col, 0) or 0
                    groups[key][feishu_col] = existing + add

    return list(groups.values())


def _has_running_job(db: Session, config_id: str) -> bool:
    """Check if there's already a running sync job for this config."""
    stmt = select(SyncJob).where(
        SyncJob.config_id == config_id,
        SyncJob.status == "running",
    )
    return db.execute(stmt).scalars().first() is not None


def _build_record_key(id_number: Optional[str], billing_period: Optional[str]) -> str:
    return f"{id_number or ''}_{billing_period or ''}"


async def push_records_to_feishu(
    db: Session,
    client: FeishuClient,
    config: SyncConfig,
    filters: dict | None,
    triggered_by: str,
) -> SyncJob:
    """Push NormalizedRecords to Feishu Bitable."""
    # Check sync lock
    if _has_running_job(db, config.id):
        raise RuntimeError(f"Another sync job is already running for config '{config.name}'")

    # Create job
    job = SyncJob(
        config_id=config.id,
        direction="push",
        status="running",
        triggered_by=triggered_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # Query records
        stmt = select(NormalizedRecord)
        if filters:
            if filters.get("region"):
                stmt = stmt.where(NormalizedRecord.region == filters["region"])
            if filters.get("company_name"):
                stmt = stmt.where(NormalizedRecord.company_name == filters["company_name"])
            if filters.get("billing_period"):
                stmt = stmt.where(NormalizedRecord.billing_period == filters["billing_period"])
        records = list(db.execute(stmt).scalars().all())

        # Transform
        if config.granularity == "summary":
            rows = _summarize_records(records, config.field_mapping)
        else:
            rows = [_record_to_feishu_row(r, config.field_mapping) for r in records]

        # Push in batches of 500
        success_count = 0
        failed_count = 0
        for chunk in _chunked(rows, 500):
            try:
                await client.batch_create_records(config.app_token, config.table_id, chunk)
                success_count += len(chunk)
            except Exception:
                failed_count += len(chunk)

        job.total_records = len(rows)
        job.success_records = success_count
        job.failed_records = failed_count
        job.status = "success" if failed_count == 0 else ("partial" if success_count > 0 else "failed")
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)[:2000]

    db.commit()
    db.refresh(job)
    return job


async def check_push_conflicts(
    db: Session,
    client: FeishuClient,
    config: SyncConfig,
    filters: dict | None,
) -> ConflictPreview | None:
    """Check for conflicts before pushing to Feishu."""
    # Fetch existing Feishu records
    feishu_data = await client.search_records(config.app_token, config.table_id)
    feishu_items = feishu_data.get("data", {}).get("items", [])
    if not feishu_items:
        return None

    # Reverse map to find id_number and billing_period Feishu columns
    reverse_mapping = {v: k for k, v in config.field_mapping.items()}
    id_col = reverse_mapping.get("id_number")
    period_col = reverse_mapping.get("billing_period")
    if not id_col or not period_col:
        return None

    # Build Feishu lookup
    feishu_lookup: dict[str, dict] = {}
    for item in feishu_items:
        fields = item.get("fields", {})
        key = _build_record_key(str(fields.get(id_col, "")), str(fields.get(period_col, "")))
        feishu_lookup[key] = fields

    # Query system records
    stmt = select(NormalizedRecord)
    if filters:
        if filters.get("region"):
            stmt = stmt.where(NormalizedRecord.region == filters["region"])
        if filters.get("company_name"):
            stmt = stmt.where(NormalizedRecord.company_name == filters["company_name"])
        if filters.get("billing_period"):
            stmt = stmt.where(NormalizedRecord.billing_period == filters["billing_period"])
    records = list(db.execute(stmt).scalars().all())

    conflicts: list[ConflictRecord] = []
    for record in records:
        key = _build_record_key(record.id_number, record.billing_period)
        if key in feishu_lookup:
            feishu_fields = feishu_lookup[key]
            sys_values: dict[str, object] = {}
            feishu_values: dict[str, object] = {}
            diff_fields: list[str] = []

            for feishu_col, sys_field in config.field_mapping.items():
                sys_val = getattr(record, sys_field, None)
                if isinstance(sys_val, Decimal):
                    sys_val = float(sys_val)
                feishu_val = feishu_fields.get(feishu_col)

                if sys_val != feishu_val:
                    sys_values[sys_field] = sys_val
                    feishu_values[sys_field] = feishu_val
                    diff_fields.append(sys_field)

            if diff_fields:
                conflicts.append(ConflictRecord(
                    record_key=key,
                    person_name=record.person_name,
                    system_values=sys_values,
                    feishu_values=feishu_values,
                    diff_fields=diff_fields,
                ))

    if not conflicts:
        return None
    return ConflictPreview(total_conflicts=len(conflicts), conflicts=conflicts)


async def pull_records_from_feishu(
    db: Session,
    client: FeishuClient,
    config: SyncConfig,
    strategy: str,
    per_record_choices: dict | None,
    triggered_by: str,
) -> SyncJob:
    """Pull records from Feishu Bitable into the system."""
    if not config.field_mapping:
        raise ValueError("Config has no field_mapping. Push records first to establish mapping.")

    job = SyncJob(
        config_id=config.id,
        direction="pull",
        status="running",
        triggered_by=triggered_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # Fetch all Feishu records (paginated)
        all_items: list[dict] = []
        page_token: str | None = None
        while True:
            result = await client.search_records(
                config.app_token, config.table_id, page_token=page_token,
            )
            data = result.get("data", {})
            items = data.get("items", [])
            all_items.extend(items)
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")

        # Reverse field mapping: {system_field: feishu_column}
        reverse_mapping = {v: k for k, v in config.field_mapping.items()}

        success_count = 0
        failed_count = 0

        for item in all_items:
            try:
                fields = item.get("fields", {})
                # Map Feishu columns to system fields
                sys_data: dict[str, Any] = {}
                for sys_field, feishu_col in reverse_mapping.items():
                    sys_data[sys_field] = fields.get(feishu_col)

                id_number = sys_data.get("id_number")
                billing_period = sys_data.get("billing_period")
                record_key = _build_record_key(id_number, billing_period)

                # Check for existing record
                existing = None
                if id_number and billing_period:
                    existing = db.execute(
                        select(NormalizedRecord).where(
                            NormalizedRecord.id_number == id_number,
                            NormalizedRecord.billing_period == billing_period,
                        )
                    ).scalars().first()

                # Apply conflict resolution
                should_update = False
                if existing:
                    if strategy == "feishu_wins":
                        should_update = True
                    elif strategy == "system_wins":
                        should_update = False
                    elif strategy == "per_record" and per_record_choices:
                        choice = per_record_choices.get(record_key, "system")
                        should_update = choice == "feishu"
                    else:
                        should_update = False

                if existing and should_update:
                    # Update existing record with Feishu data
                    for sys_field, value in sys_data.items():
                        if hasattr(existing, sys_field) and sys_field not in ("id", "batch_id", "source_file_id"):
                            setattr(existing, sys_field, value)
                    # PROVENANCE (addresses review H3)
                    existing.source_file_name = f"feishu_pull:{config.name}"
                    existing.source_row_number = 0  # no meaningful row from Feishu
                    existing.raw_header_signature = f"feishu:{config.table_id}"
                    success_count += 1
                elif not existing:
                    # Create new NormalizedRecord
                    # We need batch_id and source_file_id - use sentinel values for Feishu-pulled records
                    new_record = NormalizedRecord(
                        batch_id=str(uuid4()),
                        source_file_id=str(uuid4()),
                        source_row_number=0,
                        source_file_name=f"feishu_pull:{config.name}",
                        raw_header_signature=f"feishu:{config.table_id}",
                        **{k: v for k, v in sys_data.items() if hasattr(NormalizedRecord, k)},
                    )
                    db.add(new_record)
                    success_count += 1
                else:
                    # Existing record, system wins or no update needed
                    success_count += 1
            except Exception:
                failed_count += 1

        job.total_records = len(all_items)
        job.success_records = success_count
        job.failed_records = failed_count
        job.status = "success" if failed_count == 0 else ("partial" if success_count > 0 else "failed")
        db.commit()
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)[:2000]
        db.commit()

    db.refresh(job)
    return job


async def detect_pull_conflicts(
    db: Session,
    client: FeishuClient,
    config: SyncConfig,
) -> ConflictPreview | None:
    """Detect conflicts between Feishu records and existing system records."""
    if not config.field_mapping:
        return None

    # Fetch Feishu records
    feishu_data = await client.search_records(config.app_token, config.table_id)
    feishu_items = feishu_data.get("data", {}).get("items", [])
    if not feishu_items:
        return None

    reverse_mapping = {v: k for k, v in config.field_mapping.items()}

    conflicts: list[ConflictRecord] = []
    for item in feishu_items:
        fields = item.get("fields", {})
        sys_data: dict[str, Any] = {}
        for sys_field, feishu_col in reverse_mapping.items():
            sys_data[sys_field] = fields.get(feishu_col)

        id_number = sys_data.get("id_number")
        billing_period = sys_data.get("billing_period")

        if not id_number or not billing_period:
            continue

        existing = db.execute(
            select(NormalizedRecord).where(
                NormalizedRecord.id_number == str(id_number),
                NormalizedRecord.billing_period == str(billing_period),
            )
        ).scalars().first()

        if not existing:
            continue

        # Compare fields
        diff_fields: list[str] = []
        sys_values: dict[str, object] = {}
        feishu_values: dict[str, object] = {}

        for sys_field in reverse_mapping:
            sys_val = getattr(existing, sys_field, None)
            if isinstance(sys_val, Decimal):
                sys_val = float(sys_val)
            feishu_val = sys_data.get(sys_field)
            if sys_val != feishu_val:
                sys_values[sys_field] = sys_val
                feishu_values[sys_field] = feishu_val
                diff_fields.append(sys_field)

        if diff_fields:
            conflicts.append(ConflictRecord(
                record_key=_build_record_key(str(id_number), str(billing_period)),
                person_name=existing.person_name,
                system_values=sys_values,
                feishu_values=feishu_values,
                diff_fields=diff_fields,
            ))

    if not conflicts:
        return None
    return ConflictPreview(total_conflicts=len(conflicts), conflicts=conflicts)


def get_sync_history(
    db: Session,
    config_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SyncJob]:
    """Get sync job history ordered by created_at desc with offset+limit pagination."""
    stmt = select(SyncJob).order_by(SyncJob.created_at.desc())
    if config_id:
        stmt = stmt.where(SyncJob.config_id == config_id)
    stmt = stmt.offset(offset).limit(limit)
    return list(db.execute(stmt).scalars().all())


async def retry_sync_job(
    db: Session,
    client: FeishuClient,
    job_id: str,
    triggered_by: str,
) -> SyncJob:
    """Retry a failed sync job by creating a new job with the same parameters."""
    original = db.execute(
        select(SyncJob).where(SyncJob.id == job_id)
    ).scalars().first()

    if original is None:
        raise ValueError(f"Sync job '{job_id}' not found")
    if original.status != "failed":
        raise ValueError(f"Can only retry failed jobs. Current status: {original.status}")

    config = db.execute(
        select(SyncConfig).where(SyncConfig.id == original.config_id)
    ).scalars().first()
    if config is None:
        raise ValueError(f"SyncConfig '{original.config_id}' not found")

    if original.direction == "push":
        return await push_records_to_feishu(db, client, config, None, triggered_by)
    else:
        return await pull_records_from_feishu(db, client, config, "system_wins", None, triggered_by)

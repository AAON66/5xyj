from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from openpyxl import load_workbook

from backend.app.core.config import Settings, get_settings
from backend.app.models.enums import TemplateType
from backend.app.models.normalized_record import NormalizedRecord

from backend.app.exporters.export_utils import (
    DualTemplateExportResult,
    ExportArtifactResult,
    ExportServiceError,
    _is_exportable_record,
    _merge_export_records,
    _resolve_template_path,
)
from backend.app.exporters.salary_exporter import _rewrite_salary_sheet
from backend.app.exporters.tool_exporter import _rewrite_tool_sheet


def export_dual_templates(
    records: Iterable[NormalizedRecord],
    *,
    output_dir: str | Path | None = None,
    salary_template_path: str | Path | None = None,
    final_tool_template_path: str | Path | None = None,
    export_prefix: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> DualTemplateExportResult:
    normalized_records = _merge_export_records([record for record in records if _is_exportable_record(record)])
    resolved_settings = settings or get_settings()
    output_root = Path(output_dir) if output_dir else resolved_settings.outputs_path
    output_root.mkdir(parents=True, exist_ok=True)

    prefix = export_prefix or 'batch'
    template_inputs = [
        (TemplateType.SALARY, salary_template_path, output_root / f'{prefix}_{TemplateType.SALARY.value}.xlsx'),
        (TemplateType.FINAL_TOOL, final_tool_template_path, output_root / f'{prefix}_{TemplateType.FINAL_TOOL.value}.xlsx'),
    ]

    artifacts: list[ExportArtifactResult] = []
    for template_type, explicit_path, output_path in template_inputs:
        try:
            template_path = _resolve_template_path(explicit_path, template_type, settings=resolved_settings)
        except ExportServiceError as exc:
            artifacts.append(ExportArtifactResult(template_type.value, 'failed', None, str(exc), 0))
            continue
        artifacts.append(_export_template_variant(template_type, template_path, output_path, normalized_records))

    overall_status = 'completed' if all(item.status == 'completed' for item in artifacts) else 'failed'
    return DualTemplateExportResult(status=overall_status, artifacts=artifacts)


def _export_template_variant(
    template_type: TemplateType,
    template_path: Path,
    output_path: Path,
    records: list[NormalizedRecord],
) -> ExportArtifactResult:
    try:
        workbook = load_workbook(template_path)
        if template_type == TemplateType.SALARY:
            _rewrite_salary_sheet(workbook, records)
        else:
            _rewrite_tool_sheet(workbook, records)
        workbook.save(output_path)
        workbook.close()
        return ExportArtifactResult(template_type.value, 'completed', str(output_path), None, len(records))
    except Exception as exc:
        return ExportArtifactResult(template_type.value, 'failed', None, str(exc), 0)

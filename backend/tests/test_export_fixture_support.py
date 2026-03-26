from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from _pytest.outcomes import Failed
from openpyxl import load_workbook

from backend.app.core.config import Settings
from backend.tests.support import export_fixtures


def test_resolve_required_export_templates_uses_repo_manifest_defaults() -> None:
    templates = export_fixtures.resolve_required_export_templates()

    assert templates.manifest == export_fixtures.REGRESSION_TEMPLATE_MANIFEST
    assert templates.salary == export_fixtures.REGRESSION_TEMPLATE_DIR / 'salary-template.xlsx'
    assert templates.final_tool == export_fixtures.REGRESSION_TEMPLATE_DIR / 'final-tool-template.xlsx'


def test_resolve_required_export_templates_prefers_valid_explicit_paths(tmp_path: Path) -> None:
    defaults = export_fixtures.create_placeholder_template_pair(tmp_path / 'defaults')
    explicit = export_fixtures.create_placeholder_template_pair(tmp_path / 'explicit')
    manifest_copy = tmp_path / 'manifest.json'
    shutil.copy2(defaults.manifest, manifest_copy)

    settings = Settings(
        salary_template_path=str(explicit.salary),
        final_tool_template_path=str(explicit.final_tool),
    )

    original_dir = export_fixtures.REGRESSION_TEMPLATE_DIR
    original_manifest = export_fixtures.REGRESSION_TEMPLATE_MANIFEST
    export_fixtures.REGRESSION_TEMPLATE_DIR = defaults.manifest.parent
    export_fixtures.REGRESSION_TEMPLATE_MANIFEST = manifest_copy
    try:
        resolved = export_fixtures.resolve_required_export_templates(settings)
    finally:
        export_fixtures.REGRESSION_TEMPLATE_DIR = original_dir
        export_fixtures.REGRESSION_TEMPLATE_MANIFEST = original_manifest

    assert resolved.salary == explicit.salary
    assert resolved.final_tool == explicit.final_tool
    assert resolved.manifest == manifest_copy


def test_resolve_required_export_templates_fails_loudly_when_manifest_assets_are_missing(tmp_path: Path) -> None:
    fixture_dir = tmp_path / 'regression'
    fixture_dir.mkdir(parents=True)
    manifest = fixture_dir / 'manifest.json'
    manifest.write_text(
        '{"salary":"salary-template.xlsx","final_tool":"final-tool-template.xlsx"}',
        encoding='utf-8',
    )

    original_dir = export_fixtures.REGRESSION_TEMPLATE_DIR
    original_manifest = export_fixtures.REGRESSION_TEMPLATE_MANIFEST
    export_fixtures.REGRESSION_TEMPLATE_DIR = fixture_dir
    export_fixtures.REGRESSION_TEMPLATE_MANIFEST = manifest
    try:
        with pytest.raises(Failed, match='Missing required export templates'):
            export_fixtures.resolve_required_export_templates()
    finally:
        export_fixtures.REGRESSION_TEMPLATE_DIR = original_dir
        export_fixtures.REGRESSION_TEMPLATE_MANIFEST = original_manifest


def test_require_sample_workbook_fails_loudly_for_missing_sample() -> None:
    with pytest.raises(Failed, match='Missing required sample workbook'):
        export_fixtures.require_sample_workbook('missing-sample-keyword')


def test_create_placeholder_template_pair_creates_valid_workbooks(tmp_path: Path) -> None:
    templates = export_fixtures.create_placeholder_template_pair(tmp_path / 'placeholder')

    assert templates.salary.exists()
    assert templates.final_tool.exists()
    assert templates.manifest.exists()

    salary_workbook = load_workbook(templates.salary, data_only=False)
    tool_workbook = load_workbook(templates.final_tool, data_only=False)
    assert salary_workbook[salary_workbook.sheetnames[0]]['A1'].value == '员工姓名'
    assert str(tool_workbook[tool_workbook.sheetnames[0]]['AA7'].value).startswith('=')
    assert str(tool_workbook[tool_workbook.sheetnames[0]]['AO7'].value).startswith('=')
    salary_workbook.close()
    tool_workbook.close()

"""API compatibility tests for the exporter module split.

Ensures the public API surface of backend.app.exporters remains unchanged
after splitting template_exporter.py into multiple modules.
"""
from __future__ import annotations


def test_public_api_imports():
    """All previously public symbols are still importable from the package."""
    from backend.app.exporters import (
        DualTemplateExportResult,
        ExportArtifactResult,
        ExportServiceError,
        export_dual_templates,
    )

    assert callable(export_dual_templates)
    assert DualTemplateExportResult is not None
    assert ExportArtifactResult is not None
    assert ExportServiceError is not None


def test_public_api_no_missing_symbols():
    """The __all__ list in __init__.py matches the expected public API."""
    import backend.app.exporters as pkg

    expected = {'DualTemplateExportResult', 'ExportArtifactResult', 'ExportServiceError', 'export_dual_templates'}
    actual = set(pkg.__all__)
    assert actual == expected, f"API surface mismatch: missing={expected - actual}, extra={actual - expected}"


def test_no_circular_imports():
    """Modules can be imported independently without circular import errors."""
    import importlib

    modules = [
        'backend.app.exporters.export_utils',
        'backend.app.exporters.salary_exporter',
        'backend.app.exporters.tool_exporter',
        'backend.app.exporters.template_exporter',
        'backend.app.exporters',
    ]
    for mod_name in modules:
        importlib.import_module(mod_name)


def test_salary_headers_structure():
    """Salary headers list has expected length and key entries."""
    from backend.app.exporters.salary_exporter import SALARY_HEADERS

    assert len(SALARY_HEADERS) == 16
    assert SALARY_HEADERS[0] == '员工姓名'
    assert SALARY_HEADERS[1] == '工号'
    assert SALARY_HEADERS[-1] == '公司公积金'
    assert '个人社保承担额' not in SALARY_HEADERS
    assert '个人公积金承担额' not in SALARY_HEADERS


def test_tool_headers_structure():
    """Tool headers list has expected length and key entries."""
    from backend.app.exporters.tool_exporter import TOOL_HEADERS

    assert len(TOOL_HEADERS) == 42
    assert TOOL_HEADERS[0] == '主体'
    assert TOOL_HEADERS[1] == '区域'
    assert TOOL_HEADERS[-1] == '个人+单位合计'

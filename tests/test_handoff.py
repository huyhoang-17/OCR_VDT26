"""Test M11 (bàn giao): tính toàn vẹn plugin + CLI smoke.

Bảo đảm mọi biểu mẫu khai báo hợp lệ (strategy/normalizer mà core hỗ trợ) và
các lệnh CLI cơ bản chạy được — chống hồi quy khi thêm biểu mẫu mới sau này.
"""

from __future__ import annotations

from ocr_idp.config import load_config
from ocr_idp.extract.orchestrator import ExtractionOrchestrator
from ocr_idp.normalize.apply import NORMALIZERS
from ocr_idp.forms.base import get_form, list_forms


def _known_strategies() -> set[str]:
    return set(ExtractionOrchestrator(load_config())._extractors)


def test_all_plugins_declare_valid_schema_and_specs() -> None:
    strategies = _known_strategies()
    assert set(list_forms()) == {"account_opening_individual", "order_slip", "shareholder_list"}

    for form_type in list_forms():
        plugin = get_form(form_type)
        schema = plugin.load_schema()
        assert schema["type"] == "object" and "properties" in schema
        assert schema["properties"]["form_type"]  # mọi schema có form_type

        specs = plugin.field_specs()
        assert specs, f"{form_type}: không có field nào"
        for s in specs:
            assert s.strategy in strategies, f"{form_type}.{s.name}: strategy lạ '{s.strategy}'"
            if s.normalizer:
                assert s.normalizer in NORMALIZERS, f"{form_type}.{s.name}: normalizer lạ"
            # Trường bảng: kiểm tra normalizer của từng cột
            if s.strategy == "table":
                for col in (s.options or {}).get("columns", []):
                    nm = col.get("normalizer")
                    assert nm is None or nm in NORMALIZERS, f"{form_type}: cột {col.get('field')} normalizer lạ"


def test_required_fields_have_anchor_or_rule_or_layout() -> None:
    """Trường bắt buộc phải có cách trích (anchor/regex/options) — tránh luôn MISSING."""
    for form_type in list_forms():
        for s in get_form(form_type).field_specs():
            if s.required:
                assert s.anchor or s.regex or s.options, f"{form_type}.{s.name} bắt buộc nhưng thiếu cách trích"


# --------------------------------- CLI smoke ------------------------------- #
def test_cli_version_and_forms() -> None:
    from typer.testing import CliRunner

    from ocr_idp.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0 and "OCR-IDP" in r.stdout

    r = runner.invoke(app, ["forms"])
    assert r.exit_code == 0
    assert "order_slip" in r.stdout and "shareholder_list" in r.stdout

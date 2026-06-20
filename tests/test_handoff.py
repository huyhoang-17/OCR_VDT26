"""Test bàn giao: registry plugin + tính toàn vẹn khung trích xuất + CLI smoke.

Sau khi gỡ dữ liệu/plugin synthetic, registry chỉ còn plugin 'generic' (fallback
kết xuất OCR theo trang). Khung trích xuất theo trường (strategy/normalizer) vẫn
được giữ để thêm plugin chuyên biệt cho từng eform về sau mà không sửa core.
"""

from __future__ import annotations

from ocr_idp.config import load_config
from ocr_idp.extract.orchestrator import ExtractionOrchestrator
from ocr_idp.forms.base import get_form, list_forms
from ocr_idp.normalize.apply import NORMALIZERS


def test_generic_plugin_registered() -> None:
    assert set(list_forms()) == {"generic"}
    plugin = get_form("generic")
    assert plugin.form_type == "generic"
    assert plugin.field_specs() == []  # generic không trích theo trường


def test_extraction_framework_intact() -> None:
    """Các strategy + normalizer của core vẫn đầy đủ (sẵn sàng cho plugin mới)."""
    strategies = set(ExtractionOrchestrator(load_config())._extractors)
    assert {"anchor", "rule", "checkbox", "signature", "radio", "table", "layout", "llm"} <= strategies
    # Bộ normalizer cốt lõi vẫn còn
    for nm in ("date", "datetime", "money", "string", "account_number"):
        assert nm in NORMALIZERS, f"thiếu normalizer '{nm}'"


# --------------------------------- CLI smoke ------------------------------- #
def test_cli_version_and_forms() -> None:
    from typer.testing import CliRunner

    from ocr_idp.cli import app

    runner = CliRunner()
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0 and "OCR-IDP" in r.stdout

    r = runner.invoke(app, ["forms"])
    assert r.exit_code == 0
    assert "generic" in r.stdout

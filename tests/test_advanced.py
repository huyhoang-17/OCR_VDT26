"""Test M6: layout-based extraction + LLM (schema, availability, fallback, repair-merge).

LLM thật cần ANTHROPIC_API_KEY (chạy trong Docker/khi có key). Ở đây test logic
bằng mock — không gọi mạng.
"""

from __future__ import annotations

import numpy as np

from ocr_idp.config import load_config
from ocr_idp.extract.base import ExtractionContext, FieldSpec
from ocr_idp.extract.orchestrator import ExtractionOrchestrator
from ocr_idp.types import BBox, Line, PageImage


def _line(text, x1, y1, x2, y2, conf=1.0):
    return Line(text=text, bbox=BBox(x1, y1, x2, y2), confidence=conf)


def _ctx(lines, pages=None):
    return ExtractionContext(lines=lines, config=load_config(), pages=pages)


def _page(w=100, h=100):
    return PageImage(image=np.zeros((h, w), np.uint8), page_index=0, dpi=150)


# ------------------------------ layout_based ------------------------------- #
def test_layout_region_collects_lines_in_box() -> None:
    from ocr_idp.extract.layout_based import LayoutBasedExtractor

    lines = [_line("TRONG VUNG", 60, 5, 90, 15), _line("ngoai vung", 5, 80, 40, 92)]
    spec = FieldSpec(name="x", strategy="layout", options={"region": [0.5, 0.0, 1.0, 0.3]})
    fv = LayoutBasedExtractor(load_config()).extract(spec, _ctx(lines, pages=[_page()]))
    assert fv.raw_value == "TRONG VUNG"


def test_layout_anchor_relative_multiline() -> None:
    from ocr_idp.extract.layout_based import LayoutBasedExtractor

    lines = [
        _line("Địa chỉ:", 60, 100, 110, 114),
        _line("Số 1 Lê Lợi,", 120, 100, 260, 114),
        _line("Quận 1, TP.HCM", 120, 118, 260, 132),  # dòng dưới
    ]
    spec = FieldSpec(name="addr", strategy="layout", anchor=["Địa chỉ"], options={"max_below": 1})
    fv = LayoutBasedExtractor(load_config()).extract(spec, _ctx(lines, pages=[_page(400, 400)]))
    assert "Số 1 Lê Lợi" in fv.raw_value and "Quận 1" in fv.raw_value


# --------------------------- LLM schema/availability ----------------------- #
def test_build_schema() -> None:
    from ocr_idp.extract.llm_claude import build_schema

    specs = [
        FieldSpec(name="investor.full_name", strategy="llm", anchor=["Họ và tên"], normalizer="string"),
        FieldSpec(name="quantity", strategy="llm", normalizer="int"),
        FieldSpec(name="side", strategy="llm", choices=["MUA", "BÁN"]),
    ]
    schema = build_schema(specs)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"investor.full_name", "quantity", "side"}
    assert schema["properties"]["quantity"]["type"] == ["integer", "null"]
    assert None in schema["properties"]["side"]["enum"]


def test_is_llm_available_without_key() -> None:
    from ocr_idp.extract.llm_claude import is_llm_available

    cfg = load_config()
    # Môi trường test không có ANTHROPIC_API_KEY -> không khả dụng
    import os

    if not os.environ.get(cfg.extraction.llm.api_key_env):
        assert is_llm_available(cfg) is False


def test_claude_extractor_parses_mocked_response(monkeypatch) -> None:
    from ocr_idp.extract.llm_claude import ClaudeExtractor

    class _Block:
        type = "text"
        text = '{"investor.full_name": "Phạm Văn Hùng", "quantity": 1000}'

    class _Resp:
        content = [_Block()]

    class _Msgs:
        def create(self, **kwargs):
            return _Resp()

    class _FakeClient:
        messages = _Msgs()

    ex = ClaudeExtractor(load_config())
    monkeypatch.setattr(ex, "_get_client", lambda: _FakeClient())
    specs = [FieldSpec(name="investor.full_name", strategy="llm"), FieldSpec(name="quantity", strategy="llm", normalizer="int")]
    out = ex.extract(specs, "ho ten pham van hung ... khoi luong 1000")
    assert out["investor.full_name"] == "Phạm Văn Hùng"
    assert out["quantity"] == 1000


# ------------------------- llm strategy fallback --------------------------- #
def test_llm_field_falls_back_to_anchor_without_key() -> None:
    specs = [FieldSpec(name="x", strategy="llm", anchor=["Họ và tên"])]
    lines = [_line("Họ và tên:", 60, 100, 140, 115), _line("Nguyễn Văn A", 150, 100, 300, 115)]
    fields = ExtractionOrchestrator(load_config()).extract_fields(specs, _ctx(lines))
    assert fields["x"].raw_value == "Nguyễn Văn A"  # dùng anchor làm fallback


# ----------------------- repair-merge (mocked LLM) ------------------------- #
def test_llm_repair_merges_into_fields(monkeypatch) -> None:
    import ocr_idp.extract.llm_claude as llm_mod
    from ocr_idp.extract.base import ExtractionContext
    from ocr_idp.forms.base import FormPlugin

    cfg = load_config(overrides={"extraction.llm.enabled": True})
    monkeypatch.setattr(llm_mod, "is_llm_available", lambda c: True)

    class _FakeExtractor:
        def __init__(self, c):
            ...

        def extract(self, specs, text):
            return {"investor.full_name": "Phạm Văn Hùng"}

    monkeypatch.setattr(llm_mod, "ClaudeExtractor", _FakeExtractor)

    # Plugin tạm (1 trường anchor) thay cho plugin synthetic đã gỡ — khung trích
    # xuất theo trường + repair-merge của LLM vẫn nguyên ở FormPlugin.
    class _TmpPlugin(FormPlugin):
        form_type = "tmp_test"
        title = "tmp"

        def field_specs(self):  # type: ignore[override]
            return [FieldSpec(name="investor.full_name", strategy="anchor",
                              anchor=["Họ và tên"], normalizer="string")]

    plugin = _TmpPlugin()
    # context rỗng -> field anchor "yếu" -> repair sẽ gọi LLM
    result = plugin.extract(ExtractionContext(lines=[], config=cfg), cfg)
    fv = result.fields["investor.full_name"]
    assert fv.source == "llm"
    assert fv.value == "Phạm Văn Hùng"

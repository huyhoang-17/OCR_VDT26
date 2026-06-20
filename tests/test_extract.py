"""Test trích xuất (anchor/rule/deferred) + plugin 'generic' (kết xuất theo trang)."""

from __future__ import annotations

from ocr_idp.config import load_config
from ocr_idp.extract.anchor_label import AnchorExtractor
from ocr_idp.extract.base import ExtractionContext, FieldSpec
from ocr_idp.extract.orchestrator import ExtractionOrchestrator
from ocr_idp.extract.rule_regex import RuleExtractor
from ocr_idp.types import BBox, FieldStatus, Line


def _line(text: str, x1: float, y1: float, x2: float, y2: float, conf: float = 1.0) -> Line:
    return Line(text=text, bbox=BBox(x1, y1, x2, y2), confidence=conf)


def _ctx(lines: list[Line]) -> ExtractionContext:
    return ExtractionContext(lines=lines, config=load_config())


# ------------------------------ FieldSpec ---------------------------------- #
def test_fieldspec_from_dict() -> None:
    spec = FieldSpec.from_dict({"name": "x", "strategy": "anchor", "anchor": "Họ và tên"})
    assert spec.anchor == ["Họ và tên"]  # chuỗi -> list
    spec2 = FieldSpec.from_dict({"name": "y", "strategy": "rule", "regex": "\\d+", "khong_biet": 1})
    assert spec2.regex == "\\d+"  # key lạ bị bỏ qua


# ------------------------------ Anchor ------------------------------------- #
def test_anchor_value_to_right() -> None:
    lines = [_line("Họ và tên:", 60, 100, 140, 115), _line("Nguyễn Văn A", 150, 100, 300, 115)]
    spec = FieldSpec(name="investor.full_name", strategy="anchor", anchor=["Họ và tên"])
    fv = AnchorExtractor(load_config()).extract(spec, _ctx(lines))
    assert fv.raw_value == "Nguyễn Văn A"
    assert fv.status == FieldStatus.OK


def test_anchor_works_without_accents_like_scan() -> None:
    # Giả lập OCR scan mất dấu: nhãn "ho va ten" vẫn khớp anchor "Họ và tên"
    lines = [_line("ho va ten", 60, 100, 140, 115), _line("Nguyen Van A", 150, 100, 300, 115)]
    spec = FieldSpec(name="investor.full_name", strategy="anchor", anchor=["Họ và tên"])
    fv = AnchorExtractor(load_config()).extract(spec, _ctx(lines))
    assert fv.raw_value == "Nguyen Van A"


def test_anchor_disambiguates_short_label() -> None:
    # "Số" phải khớp dòng "Số:" chứ không phải "Số tài khoản:"
    lines = [
        _line("Số tài khoản:", 60, 60, 160, 75),
        _line("204C161559", 170, 60, 280, 75),
        _line("Số:", 60, 100, 90, 115),
        _line("819600133", 100, 100, 220, 115),
    ]
    spec = FieldSpec(name="investor.id_document.number", strategy="anchor", anchor=["Số"])
    fv = AnchorExtractor(load_config()).extract(spec, _ctx(lines))
    assert fv.raw_value == "819600133"


def test_anchor_missing() -> None:
    spec = FieldSpec(name="x", strategy="anchor", anchor=["Không có nhãn này"])
    fv = AnchorExtractor(load_config()).extract(spec, _ctx([_line("abc", 0, 0, 10, 10)]))
    assert fv.status == FieldStatus.MISSING


# ------------------------------- Rule -------------------------------------- #
def test_rule_regex_registration_date() -> None:
    lines = [_line("Hà Nội, ngày 10 tháng 09 năm 2024", 200, 600, 450, 615)]
    spec = FieldSpec(
        name="registration_date", strategy="rule",
        regex=r"ngay\s+\d{1,2}\s+thang\s+\d{1,2}\s+nam\s+\d{4}",
    )
    fv = RuleExtractor(load_config()).extract(spec, _ctx(lines))
    assert "10" in fv.raw_value and "2024" in fv.raw_value


# --------------------------- Orchestrator/deferred ------------------------- #
def test_orchestrator_checkbox_without_image() -> None:
    # Checkbox là extractor THẬT (M5) nhưng thiếu ảnh -> trả [] + cảnh báo
    specs = [FieldSpec(name="account.account_types", strategy="checkbox", options={"thường": "Thường"})]
    fields = ExtractionOrchestrator(load_config()).extract_fields(specs, _ctx([]))
    fv = fields["account.account_types"]
    assert fv.value == [] and fv.status == FieldStatus.MISSING


def test_orchestrator_llm_without_anchor_or_regex_is_missing() -> None:
    # strategy 'llm' nhưng không có anchor/regex và không có LLM -> MISSING + cảnh báo
    specs = [FieldSpec(name="x", strategy="llm")]
    fv = ExtractionOrchestrator(load_config()).extract_fields(specs, _ctx([]))["x"]
    assert fv.status == FieldStatus.MISSING
    assert any("llm" in w.lower() for w in fv.warnings)


# --------------------------- Plugin 'generic' ------------------------------ #
def test_generic_plugin_groups_lines_by_page() -> None:
    """Plugin generic gom dòng OCR theo page_index -> khối text từng trang."""
    from ocr_idp.forms.base import get_form, list_forms

    assert "generic" in list_forms()
    plugin = get_form("generic")
    lines = [
        _line("trang 0 dong 1", 0, 0, 100, 12),               # page_index mặc định = 0
        _line("trang 0 dong 2", 0, 20, 100, 32),
        Line(text="trang 1 dong 1", bbox=BBox(0, 0, 100, 12), page_index=1),
    ]
    er = plugin.extract(_ctx(lines), load_config())
    out = plugin.assemble(er)

    assert out["form_type"] == "generic"
    assert out["page_count"] == 2
    assert [p["page_index"] for p in out["pages"]] == [0, 1]
    assert out["pages"][0]["n_lines"] == 2
    assert out["pages"][1]["lines"] == ["trang 1 dong 1"]
    assert "_meta" in out

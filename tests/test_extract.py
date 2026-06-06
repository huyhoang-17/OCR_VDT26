"""Test M4: trích xuất (anchor/rule/deferred), plugin Form A, end-to-end PDF."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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


# ------------------------------- Plugin ------------------------------------ #
def test_form_plugin_registered_and_loads() -> None:
    from ocr_idp.forms.base import get_form, list_forms

    assert "account_opening_individual" in list_forms()
    plugin = get_form("account_opening_individual")
    assert plugin.load_schema()["type"] == "object"
    specs = plugin.field_specs()
    assert any(s.name == "investor.full_name" for s in specs)


def test_form_classify() -> None:
    from ocr_idp.forms.base import get_form

    plugin = get_form("account_opening_individual")
    text = "giay de nghi mo tai khoan giao dich chung khoan thong tin nha dau tu"
    assert plugin.classify(text) > 0.5


def test_assemble_dotpath() -> None:
    from ocr_idp.forms.base import get_form
    from ocr_idp.types import ExtractionResult, FieldValue

    plugin = get_form("account_opening_individual")
    er = ExtractionResult(form_type="account_opening_individual")
    er.fields["investor.full_name"] = FieldValue(name="investor.full_name", value="Nguyễn Văn A", confidence=1.0)
    er.fields["account.account_number"] = FieldValue(name="account.account_number", value="204C1", confidence=0.9)
    out = plugin.assemble(er)
    assert out["form_type"] == "account_opening_individual"
    assert out["investor"]["full_name"] == "Nguyễn Văn A"
    assert out["account"]["account_number"] == "204C1"
    assert "_meta" in out and "confidence" in out["_meta"]


# --------------------------- End-to-end (PDF) ------------------------------ #
def test_end_to_end_pdf_matches_ground_truth() -> None:
    pytest.importorskip("fitz")
    sample = Path("data/synthetic/account_opening_individual/sample_01.pdf")
    gt_path = Path("data/ground_truth/account_opening_individual/sample_01.json")
    if not sample.exists() or not gt_path.exists():
        pytest.skip("Chưa có dữ liệu synthetic (chạy: ocr-idp make-data)")

    from ocr_idp.pipeline import Pipeline

    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    result = Pipeline(load_config()).run(sample)  # form_type tự đoán

    assert result.form_type == "account_opening_individual"
    out = result.output_json
    # Text-layer cho kết quả chính xác tuyệt đối -> khớp ground-truth
    assert out["investor"]["full_name"] == gt["investor"]["full_name"]
    assert out["investor"]["id_document"]["number"] == gt["investor"]["id_document"]["number"]
    assert out["investor"]["email"] == gt["investor"]["email"]
    assert out["registration_date"] == gt["registration_date"]
    assert out["investor"]["date_of_birth"] == gt["investor"]["date_of_birth"]


@pytest.mark.parametrize("stem", ["sample_01", "sample_02", "sample_03"])
def test_checkbox_signature_match_gt_pdf(stem: str) -> None:
    """M5: checkbox (account_types/services) + chữ ký khớp ground-truth trên PDF."""
    pytest.importorskip("fitz")
    pdf = Path(f"data/synthetic/account_opening_individual/{stem}.pdf")
    gt_path = Path(f"data/ground_truth/account_opening_individual/{stem}.json")
    if not pdf.exists() or not gt_path.exists():
        pytest.skip("Chưa có dữ liệu synthetic")

    from ocr_idp.pipeline import Pipeline

    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    out = Pipeline(load_config()).run(pdf).output_json
    assert sorted(out["account"]["account_types"]) == sorted(gt["account"]["account_types"])
    assert sorted(out["account"]["services"]) == sorted(gt["account"]["services"])
    assert out["signature_present"] == gt["signature_present"]

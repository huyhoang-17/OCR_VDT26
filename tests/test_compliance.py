"""Business-rule engine, benchmark lỗi nhân tạo và xuất biên bản."""

from __future__ import annotations

import zipfile
from io import BytesIO

from ocr_idp.compliance import CheckStatus, ComplianceEngine
from ocr_idp.compliance.evaluation import evaluate_mutations
from ocr_idp.compliance.parsers import parse_date, parse_number
from ocr_idp.compliance.report import to_docx, to_markdown, to_pdf
from ocr_idp.compliance.service import build_compliance_report
from ocr_idp.compliance.summary import ComplianceSummarizer


def _eform1() -> dict:
    return {
        "form_id": "eform1",
        "results": {
            "NgaythangnamzzValue": "2026-04-21T00:00:00+00:00",
            "NgaycapGCNUBCKzzValue": "2025-10-15T00:00:00+00:00",
            "MenhgiacophieuzzValue": "10.000",
            "TongsoluongcophieuphathanhzzValue": "20.000.000",
            "TongsovondahuydongzzValue": "200.000.000.000",
            "SovondahuydongzzValue": "150.000.000.000",
            "NgayketthucdotchaobanzzValue": "2025-11-30T00:00:00+00:00",
        },
    }


def test_vietnamese_number_and_date_parsers() -> None:
    assert parse_number("500 tỷ đồng") == 500_000_000_000
    assert parse_number("1.234.567") == 1_234_567
    assert parse_number("8,5%") == 8.5
    assert parse_date("21/04/2026").isoformat() == "2026-04-21"


def test_eform1_rules_pass_and_do_not_mutate_input() -> None:
    document = _eform1()
    original = dict(document["results"])
    report = ComplianceEngine().check(document)
    assert report.overall_status == "compliant"
    assert report.counts == {"pass": 4, "violation": 0, "skipped": 0}
    assert document["results"] == original


def test_arithmetic_and_date_violations_are_detected() -> None:
    document = _eform1()
    document["results"]["TongsovondahuydongzzValue"] = "250.000.000.000"
    document["results"]["NgaythangnamzzValue"] = "2025-01-01"
    report = ComplianceEngine().check(document)
    violated = {c.rule_id for c in report.checks if c.status == CheckStatus.VIOLATION}
    assert {"eform1.capital_product", "eform1.report_after_offering"} <= violated
    assert report.overall_status == "non_compliant"


def test_missing_cross_field_data_is_skipped_not_a_violation() -> None:
    document = _eform1()
    document["results"].pop("MenhgiacophieuzzValue")
    report = ComplianceEngine().check(document)
    target = next(c for c in report.checks if c.rule_id == "eform1.capital_product")
    assert target.status == CheckStatus.SKIPPED


def test_unknown_form_is_not_reported_as_compliant() -> None:
    report = build_compliance_report({"form_id": "unknown", "results": {}})
    assert report.overall_status == "not_assessed"
    assert report.warnings


def test_synthetic_mutation_benchmark_scores_expected_rule() -> None:
    evaluated = evaluate_mutations([_eform1()])
    assert len(evaluated.cases) == 4
    assert (evaluated.tp, evaluated.fp, evaluated.fn) == (4, 0, 0)
    assert evaluated.precision == evaluated.recall == evaluated.f1 == 1.0


def test_llm_failure_falls_back_without_changing_checks(monkeypatch) -> None:
    report = ComplianceEngine().check(_eform1())
    monkeypatch.setattr(
        ComplianceSummarizer, "_openai",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    result = ComplianceSummarizer().summarize(report, provider="openai")
    assert result.summary_source == "deterministic_fallback"
    assert "4 kiểm tra" in result.summary
    assert len(result.checks) == 4
    # Payload LLM chỉ chứa kết quả đã tính, không chứa toàn bộ JSON nguồn/field map.
    assert set(result.llm_payload()) == {"form_type", "overall_status", "counts", "violations"}


def test_markdown_docx_and_pdf_exports_are_valid() -> None:
    report = build_compliance_report(_eform1(), provider="deterministic")
    assert "BIÊN BẢN KIỂM TRA TUÂN THỦ" in to_markdown(report)

    docx = to_docx(report)
    with zipfile.ZipFile(BytesIO(docx)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
        assert "BIÊN BẢN KIỂM TRA TUÂN THỦ" in xml
        assert "eform1.capital_product" in xml

    pdf = to_pdf(report)
    assert pdf.startswith(b"%PDF") and len(pdf) > 1000


def test_every_real_form_has_declarative_rules() -> None:
    registry = ComplianceEngine().registry
    for form_type in ("eform1", "eform5", "eform7", "eform69", "eform85", "eform92", "eform93", "eform94", "eform100"):
        fields, rules = registry.load(form_type)
        assert fields and rules, form_type

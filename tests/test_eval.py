"""Test M9: metrics so khớp (scalar/set/table + phân loại lỗi) + tổng hợp report.

End-to-end `evaluate_dataset` trên PDF text-layer -> kỳ vọng accuracy ~100%
(fast path chính xác tuyệt đối).
"""

from __future__ import annotations

import pytest

from ocr_idp.config import load_config
from ocr_idp.eval.metrics import (
    collect_fields,
    compare_documents,
    compare_scalar,
    compare_set,
    compare_table,
)


# ------------------------------- collect_fields --------------------------- #
def test_collect_fields_flattens_and_classifies() -> None:
    doc = {
        "form_type": "x", "_meta": {"a": 1},
        "investor": {"full_name": "A", "id_document": {"number": "012"}},
        "account": {"account_types": ["thường", "ký quỹ"]},
        "shareholders": [{"no": 1, "full_name": "A"}],
    }
    fields = collect_fields(doc)
    assert "form_type" not in fields and "_meta" not in fields  # bỏ qua
    assert fields["investor.full_name"] == ("scalar", "A")
    assert fields["investor.id_document.number"][0] == "scalar"
    assert fields["account.account_types"][0] == "set"
    assert fields["shareholders"][0] == "table"


# --------------------------------- scalar --------------------------------- #
def test_scalar_exact_and_numeric() -> None:
    assert compare_scalar("p", "Nguyễn Văn A", "Nguyễn Văn A").exact
    assert compare_scalar("p", 1000, 1000).exact
    assert compare_scalar("p", None, None).exact          # null đúng = khớp


def test_scalar_missing_and_ocr_and_format_errors() -> None:
    miss = compare_scalar("p", None, "Giá trị")
    assert miss.error_type == "missing" and not miss.exact

    # mất dấu (de-accent giống nhau) -> ocr_error, độ tương đồng cao
    ocr = compare_scalar("p", "Pham Van Hung", "Phạm Văn Hùng")
    assert ocr.error_type == "ocr_error" and ocr.similarity > 0.8

    fmt = compare_scalar("p", "XYZ123", "Phạm Văn Hùng")
    assert fmt.error_type == "format_error"

    extra = compare_scalar("p", "thừa", None)
    assert extra.error_type == "extra"


# ----------------------------------- set ---------------------------------- #
def test_set_compare() -> None:
    assert compare_set("p", ["thường", "ký quỹ"], ["ký quỹ", "thường"]).exact  # khác thứ tự vẫn khớp
    partial = compare_set("p", ["thường"], ["thường", "ký quỹ"])
    assert not partial.exact and 0.0 < partial.similarity < 1.0


# ---------------------------------- table --------------------------------- #
def test_table_compare_exact_and_partial() -> None:
    gt = [{"no": 1, "full_name": "A", "shares": 1000}, {"no": 2, "full_name": "B", "shares": 2000}]
    assert compare_table("p", list(gt), gt).exact

    # sai 1 ô -> không exact, similarity = 5/6
    pred = [{"no": 1, "full_name": "A", "shares": 1000}, {"no": 2, "full_name": "B", "shares": 9999}]
    out = compare_table("p", pred, gt)
    assert not out.exact and abs(out.similarity - 5 / 6) < 1e-6


def test_compare_documents_perfect_match() -> None:
    gt = {"form_type": "f", "a": "x", "b": {"c": 1}, "_meta": {"z": 9}}
    pred = {"form_type": "f", "a": "x", "b": {"c": 1}, "_meta": {"different": 0}}
    outcomes = compare_documents(pred, gt)
    assert all(o.exact for o in outcomes) and len(outcomes) == 2  # a, b.c (bỏ _meta/form_type)


# ----------------------------- end-to-end PDF ----------------------------- #
def test_evaluate_dataset_pdf_high_accuracy() -> None:
    pytest.importorskip("fitz")
    from pathlib import Path

    if not Path("data/ground_truth").exists():
        pytest.skip("Chưa có ground-truth (chạy: ocr-idp make-data)")

    from ocr_idp.eval.report import evaluate_dataset, to_csv, to_markdown

    report = evaluate_dataset(config=load_config(), kind="pdf")
    assert report.overall.n_samples >= 3
    # Text-layer là fast path chính xác -> accuracy trường rất cao
    assert report.overall.field_accuracy >= 0.95
    assert report.overall.form_exact_rate >= 0.5
    # report render được
    assert "Đánh giá so ground-truth" in to_markdown(report)
    assert to_csv(report).splitlines()[0].startswith("field,")


def test_evaluate_single_form() -> None:
    pytest.importorskip("fitz")
    from pathlib import Path

    if not Path("data/ground_truth/order_slip").exists():
        pytest.skip("Chưa có ground-truth")

    from ocr_idp.eval.report import evaluate_dataset

    report = evaluate_dataset(config=load_config(), kind="pdf", forms=["order_slip"])
    assert set(report.form_aggs) == {"order_slip"}
    assert report.overall.field_accuracy >= 0.95

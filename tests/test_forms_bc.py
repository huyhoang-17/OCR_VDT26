"""Test M7: chuẩn hóa mở rộng + Radio/Table extractor + plugin Form B & C.

End-to-end chạy trên PDF text-layer (fast path) -> kết quả chính xác tuyệt đối,
khớp ground-truth (gồm cả mảng bảng cổ đông của Form C).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from ocr_idp.config import load_config
from ocr_idp.extract.base import ExtractionContext, FieldSpec
from ocr_idp.types import BBox, FieldStatus, Line, PageImage


def _line(text, x1, y1, x2, y2, conf=1.0):
    return Line(text=text, bbox=BBox(x1, y1, x2, y2), confidence=conf)


def _ctx(lines, pages=None):
    return ExtractionContext(lines=lines, config=load_config(), pages=pages)


# =============================== Normalizers =============================== #
def test_parse_float_percent_variants() -> None:
    from ocr_idp.normalize.numbers import parse_float

    assert parse_float("12.34")[0] == 12.34
    assert parse_float("12,34")[0] == 12.34       # dấu phẩy thập phân kiểu Việt
    assert parse_float("50,00%")[0] == 50.0       # có ký hiệu %
    assert parse_float("1.234,5")[0] == 1234.5    # chấm nghìn + phẩy thập phân
    assert parse_float("abc")[0] is None


def test_parse_price_market_order_is_none_without_warning() -> None:
    from ocr_idp.normalize.numbers import parse_price

    val, warns = parse_price("(theo lệnh)")
    assert val is None and warns == []            # lệnh thị trường -> trống hợp lệ
    assert parse_price("85.000")[0] == 85000


def test_parse_datetime_iso() -> None:
    from ocr_idp.normalize.dates import parse_datetime

    assert parse_datetime("09:30 ngày 15/01/2025")[0] == "2025-01-15T09:30"
    assert parse_datetime("15/01/2025 9h05")[0] == "2025-01-15T09:05"
    assert parse_datetime("ngày 15/01/2025")[0] == "2025-01-15"   # thiếu giờ -> chỉ ngày


def test_norm_symbol() -> None:
    from ocr_idp.normalize.apply import _norm_symbol

    assert _norm_symbol(" vnm ")[0] == "VNM"
    assert _norm_symbol("fpt")[0] == "FPT"


# =============================== RadioExtractor ============================ #
def test_radio_without_image_is_missing() -> None:
    from ocr_idp.extract.radio_fields import RadioExtractor

    spec = FieldSpec(name="side", strategy="radio", options={"MUA": "MUA", "BÁN": "BÁN"})
    fv = RadioExtractor().extract(spec, _ctx([]))
    assert fv.value is None and fv.status == FieldStatus.MISSING


def test_radio_picks_ticked_option_on_drawn_image() -> None:
    import cv2

    # Ảnh trắng + 2 ô: ô "MUA" được tick (vẽ X), ô "BÁN" để trống.
    img = np.full((120, 240), 255, np.uint8)
    # ô MUA (ticked): hộp [30..48] x [22..40] + dấu X
    cv2.rectangle(img, (30, 22), (48, 40), 0, 1)
    cv2.line(img, (32, 24), (46, 38), 0, 2)
    cv2.line(img, (32, 38), (46, 24), 0, 2)
    # ô BÁN (untick): chỉ có viền hộp
    cv2.rectangle(img, (30, 72), (48, 90), 0, 1)

    lines = [_line("MUA", 54, 22, 90, 40), _line("BÁN", 54, 72, 90, 90)]
    page = PageImage(image=img, page_index=0, dpi=150)
    from ocr_idp.extract.radio_fields import RadioExtractor

    spec = FieldSpec(name="side", strategy="radio", options={"MUA": "MUA", "BÁN": "BÁN"})
    fv = RadioExtractor().extract(spec, _ctx(lines, pages=[page]))
    assert fv.value == "MUA"


# =============================== TableExtractor ============================ #
def test_table_extractor_parses_rows() -> None:
    from ocr_idp.extract.table_extract import TableExtractor

    lines = [
        # Tiêu đề (y ~ 10)
        _line("STT", 50, 8, 72, 22), _line("Họ và tên", 100, 8, 180, 22),
        _line("Số CMND/CCCD", 220, 8, 330, 22), _line("Số lượng CP", 360, 8, 450, 22),
        _line("Tỷ lệ (%)", 470, 8, 540, 22),
        # Dòng 1 (y ~ 30)
        _line("1", 56, 28, 66, 42), _line("Nguyễn Văn A", 100, 28, 200, 42),
        _line("012345678901", 220, 28, 330, 42), _line("1.000", 410, 28, 450, 42),
        _line("50,00", 500, 28, 540, 42),
        # Dòng 2 (y ~ 50)
        _line("2", 56, 48, 66, 62), _line("Trần Thị B", 100, 48, 200, 62),
        _line("987654321", 220, 48, 330, 62), _line("1.000", 410, 48, 450, 62),
        _line("50.00", 500, 48, 540, 62),
        # Footer -> stop
        _line("Tổng cộng: 2.000 cổ phần / 2 cổ đông", 50, 70, 400, 84),
    ]
    spec = FieldSpec(name="shareholders", strategy="table", options={
        "key_field": "full_name",
        "stop_keywords": ["Tổng cộng"],
        "columns": [
            {"field": "no", "header": ["STT"], "normalizer": "int"},
            {"field": "full_name", "header": ["Họ và tên"], "normalizer": "string"},
            {"field": "id_number", "header": ["Số CMND/CCCD"], "normalizer": "id_number"},
            {"field": "shares", "header": ["Số lượng CP"], "normalizer": "int"},
            {"field": "ratio_percent", "header": ["Tỷ lệ (%)"], "normalizer": "percent"},
        ],
    })
    fv = TableExtractor(load_config()).extract(spec, _ctx(lines))
    assert fv.status == FieldStatus.OK
    rows = fv.value
    assert len(rows) == 2
    assert rows[0] == {"no": 1, "full_name": "Nguyễn Văn A",
                       "id_number": "012345678901", "shares": 1000, "ratio_percent": 50.0}
    assert rows[1]["full_name"] == "Trần Thị B" and rows[1]["shares"] == 1000
    assert rows[1]["ratio_percent"] == 50.0   # '50.00' -> 50.0


def test_table_no_header_is_missing() -> None:
    from ocr_idp.extract.table_extract import TableExtractor

    spec = FieldSpec(name="shareholders", strategy="table", options={
        "columns": [{"field": "full_name", "header": ["Không tồn tại nhãn"]}],
    })
    fv = TableExtractor(load_config()).extract(spec, _ctx([_line("abc", 0, 0, 10, 10)]))
    assert fv.status == FieldStatus.MISSING and fv.value == []


# ============================== Classification ============================= #
@pytest.mark.parametrize("form_type,text", [
    ("order_slip", "cong ty co phan chung khoan abc phieu lenh giao dich so tai khoan san lenh ma ck khoi luong gia loai lenh kenh"),
    ("shareholder_list", "danh sach nguoi so huu chung khoan to chuc phat hanh ma ck stt ho va ten so cmnd so luong cp ty le tong cong co phan co dong"),
])
def test_detect_form_bc(form_type: str, text: str) -> None:
    from ocr_idp.forms.base import detect_form

    assert detect_form(text) == form_type


# ============================== End-to-end PDF ============================= #
@pytest.mark.parametrize("stem", ["sample_01", "sample_02", "sample_03"])
def test_order_slip_end_to_end(stem: str) -> None:
    pytest.importorskip("fitz")
    pdf = Path(f"data/synthetic/order_slip/{stem}.pdf")
    gt_path = Path(f"data/ground_truth/order_slip/{stem}.json")
    if not pdf.exists() or not gt_path.exists():
        pytest.skip("Chưa có dữ liệu synthetic (chạy: ocr-idp make-data)")

    from ocr_idp.pipeline import Pipeline

    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    out = Pipeline(load_config()).run(pdf).output_json
    assert out["form_type"] == "order_slip"
    for k in ["account_number", "investor_name", "exchange", "side", "security_symbol",
              "order_type", "quantity", "price", "order_datetime", "channel"]:
        assert out.get(k) == gt.get(k), f"{stem}.{k}: {out.get(k)!r} != {gt.get(k)!r}"


@pytest.mark.parametrize("stem", ["sample_01", "sample_02", "sample_03"])
def test_shareholder_list_end_to_end(stem: str) -> None:
    pytest.importorskip("fitz")
    pdf = Path(f"data/synthetic/shareholder_list/{stem}.pdf")
    gt_path = Path(f"data/ground_truth/shareholder_list/{stem}.json")
    if not pdf.exists() or not gt_path.exists():
        pytest.skip("Chưa có dữ liệu synthetic (chạy: ocr-idp make-data)")

    from ocr_idp.pipeline import Pipeline

    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    out = Pipeline(load_config()).run(pdf).output_json
    assert out["form_type"] == "shareholder_list"
    for k in ["issuer_name", "security_symbol", "report_date", "total_shares", "total_shareholders"]:
        assert out.get(k) == gt.get(k), f"{stem}.{k}: {out.get(k)!r} != {gt.get(k)!r}"
    # Bảng cổ đông: khớp từng dòng/cột
    assert out["shareholders"] == gt["shareholders"]

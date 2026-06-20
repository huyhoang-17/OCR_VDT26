"""Test M8: 3 engine OCR mới (Tesseract/EasyOCR/Paddle).

Logic parse của từng engine được tách thành hàm tĩnh -> test KHÔNG cần cài
torch/paddle/tesseract-binary. Availability-gating test theo điều kiện cài đặt.
"""

from __future__ import annotations

import pytest

from ocr_idp.ocr.registry import available_engines, get_engine


# ------------------------------- registry --------------------------------- #
def test_all_five_engines_registered() -> None:
    engines = available_engines()
    for name in ("rapidocr", "vietocr", "tesseract", "easyocr", "paddle"):
        assert name in engines


@pytest.mark.parametrize("name", ["tesseract", "easyocr", "paddle"])
def test_unavailable_engine_raises_clear_error(name: str) -> None:
    from ocr_idp.ocr.registry import _REGISTRY, _ensure_loaded

    _ensure_loaded()
    cls = _REGISTRY[name]
    if not cls.is_available():  # host thiếu binary/torch/paddle -> báo lỗi rõ ràng
        with pytest.raises(RuntimeError):
            get_engine(name)


# ------------------------------- Tesseract --------------------------------- #
def test_tesseract_group_lines_parses_words_into_lines() -> None:
    from ocr_idp.ocr.tesseract_engine import TesseractEngine

    data = {
        "text": ["Họ", "và", "tên", "", "Nguyễn"],
        "conf": ["95", "90", "-1", "0", "80"],   # -1/empty -> bị loại
        "block_num": [1, 1, 1, 1, 1],
        "par_num": [1, 1, 1, 1, 1],
        "line_num": [1, 1, 1, 1, 2],
        "left": [10, 40, 70, 0, 10],
        "top": [5, 5, 5, 5, 30],
        "width": [25, 20, 25, 0, 60],
        "height": [14, 14, 14, 0, 14],
    }
    lines = TesseractEngine._group_lines(data, min_conf=0.3)
    lines.sort(key=lambda ln: ln.bbox.y1)
    assert [ln.text for ln in lines] == ["Họ và", "Nguyễn"]
    assert abs(lines[0].confidence - 0.925) < 1e-6   # (95+90)/2/100
    assert lines[0].bbox.x2 == 60


# ------------------------------- EasyOCR ----------------------------------- #
def test_easyocr_lines_from_filters_low_conf() -> None:
    from ocr_idp.ocr.easyocr_engine import EasyOCREngine

    raw = [
        ([[0, 0], [100, 0], [100, 20], [0, 20]], "Xin chào", 0.88),
        ([[0, 30], [50, 30], [50, 50], [0, 50]], "abc", 0.10),  # < ngưỡng -> loại
    ]
    lines = EasyOCREngine._lines_from(raw, min_conf=0.3)
    assert len(lines) == 1
    assert lines[0].text == "Xin chào" and abs(lines[0].confidence - 0.88) < 1e-6


# -------------------------------- Paddle ----------------------------------- #
def test_paddle_lines_from_nested_structure() -> None:
    from ocr_idp.ocr.paddle_engine import PaddleOCREngine

    raw = [[  # lớp "theo trang"
        [[[0, 0], [80, 0], [80, 18], [0, 18]], ("Cổ đông", 0.93)],
        [[[0, 20], [60, 20], [60, 40], [0, 40]], ("x", 0.05)],  # < ngưỡng -> loại
    ]]
    lines = PaddleOCREngine._lines_from(raw, min_conf=0.3)
    assert len(lines) == 1
    assert lines[0].text == "Cổ đông" and abs(lines[0].confidence - 0.93) < 1e-6

"""Test M5: phát hiện checkbox, chữ ký, và ô bảng (dùng ảnh tổng hợp + dữ liệu thật)."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from ocr_idp.layout.checkbox import detect_checkbox_state
from ocr_idp.layout.signature import detect_signature
from ocr_idp.layout.tables import detect_table_cells, has_table
from ocr_idp.types import BBox


# ------------------------------- checkbox ---------------------------------- #
def test_checkbox_empty_vs_ticked() -> None:
    img = np.full((100, 200), 255, np.uint8)
    cv2.rectangle(img, (20, 40), (50, 70), 0, 2)  # ô trống
    label = BBox(60, 40, 120, 70)  # nhãn bên phải ô

    ticked, box, ratio = detect_checkbox_state(img, label)
    assert box is not None and ticked is False

    cv2.line(img, (22, 42), (48, 68), 0, 2)  # vẽ dấu X
    cv2.line(img, (22, 68), (48, 42), 0, 2)
    ticked2, _box2, ratio2 = detect_checkbox_state(img, label)
    assert ticked2 is True
    assert ratio2 > ratio


def test_checkbox_wide_rect_rejected() -> None:
    # Hình chữ nhật dẹt (không phải ô vuông) bị bộ lọc tỉ lệ loại -> không tick
    img = np.full((100, 220), 255, np.uint8)
    cv2.rectangle(img, (20, 50), (120, 64), 0, 2)  # rộng/dẹt, aspect ~7
    label = BBox(130, 48, 190, 68)
    ticked, _box, _ratio = detect_checkbox_state(img, label)
    assert ticked is False


# ------------------------------ signature ---------------------------------- #
def test_signature_blank_vs_signed() -> None:
    img = np.full((220, 220), 255, np.uint8)
    label = BBox(50, 40, 150, 56)
    assert detect_signature(img, label)[0] is False

    cv2.line(img, (60, 85), (120, 105), 0, 3)
    cv2.line(img, (120, 85), (150, 110), 0, 3)
    assert detect_signature(img, label)[0] is True


# -------------------------------- tables ----------------------------------- #
def test_detect_table_cells_synthetic() -> None:
    img = np.full((300, 400), 255, np.uint8)
    # lưới 3 cột x 3 hàng
    for x in (20, 140, 260, 380):
        cv2.line(img, (x, 20), (x, 260), 0, 2)
    for y in (20, 100, 180, 260):
        cv2.line(img, (20, y), (380, y), 0, 2)
    cells = detect_table_cells(img)
    assert len(cells) >= 6
    assert has_table(img)


def test_detect_table_on_real_pdf_scan() -> None:
    """has_table trên trang PDF thật (form_94 — tài liệu nhiều trang dạng scan)."""
    pytest.importorskip("fitz")
    sample = Path("data/raw/form_94.pdf")
    if not sample.exists():
        pytest.skip("Chưa có dữ liệu thật data/raw/form_94.pdf")
    from ocr_idp.preprocess.pdf_render import load_pages

    # Chỉ kiểm has_table chạy được & trả bool trên ảnh thật (không ép có bảng,
    # vì không phải trang nào cũng có lưới kẻ).
    pages = load_pages(sample, target_dpi=150)
    assert isinstance(has_table(pages[0].image), bool)

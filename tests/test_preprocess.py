"""Test M2: các bước tiền xử lý (chủ yếu dùng OpenCV/numpy; PDF/sauvola skip nếu thiếu lib)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ocr_idp.config import PreprocessConfig
from ocr_idp.preprocess.base import limit_size, rotate_image, to_bgr, to_gray
from ocr_idp.preprocess.binarize import binarize, enhance_contrast
from ocr_idp.preprocess.crop import auto_crop
from ocr_idp.preprocess.denoise import denoise
from ocr_idp.preprocess.deskew import deskew, estimate_skew_angle
from ocr_idp.types import PageImage


def _doc_image(h: int = 700, w: int = 500) -> np.ndarray:
    """Ảnh xám giả lập tài liệu: nền trắng + vài 'dòng chữ' đen nằm ngang."""
    img = np.full((h, w), 255, dtype=np.uint8)
    for y in range(60, h - 60, 40):
        img[y : y + 12, 50 : w - 50] = 0
    return img


# --------------------------- helpers cơ bản -------------------------------- #
def test_to_gray_to_bgr_roundtrip() -> None:
    bgr = np.zeros((10, 20, 3), dtype=np.uint8)
    gray = to_gray(bgr)
    assert gray.shape == (10, 20)
    assert to_gray(gray).shape == (10, 20)  # idempotent
    assert to_bgr(gray).shape == (10, 20, 3)


def test_limit_size() -> None:
    img = np.zeros((4000, 2000), dtype=np.uint8)
    out, scale = limit_size(img, 2500)
    assert max(out.shape) == 2500
    assert scale == pytest.approx(2500 / 4000)
    out2, scale2 = limit_size(np.zeros((100, 100), np.uint8), 2500)
    assert scale2 == 1.0 and out2.shape == (100, 100)


# ------------------------------ deskew ------------------------------------- #
def test_estimate_skew_recovers_angle() -> None:
    img = _doc_image()
    skewed = rotate_image(img, 5.0, border=255)  # nghiêng +5 độ
    angle = estimate_skew_angle(skewed, max_angle=10, step=0.5)
    # Góc hiệu chỉnh phải ~ -5 để bù lại
    assert angle == pytest.approx(-5.0, abs=1.5)


def test_deskew_straight_image_is_noop() -> None:
    img = _doc_image()
    out, angle = deskew(img)
    assert abs(angle) < 1.0
    assert out.shape == img.shape


# ---------------------------- binarize/contrast ---------------------------- #
def test_binarize_otsu_adaptive_none() -> None:
    img = _doc_image()
    assert set(np.unique(binarize(img, "otsu"))).issubset({0, 255})
    assert set(np.unique(binarize(img, "adaptive"))).issubset({0, 255})
    assert np.array_equal(binarize(img, "none"), img)
    with pytest.raises(ValueError):
        binarize(img, "khong_ton_tai")


def test_binarize_sauvola_if_available() -> None:
    pytest.importorskip("skimage")
    img = _doc_image()
    out = binarize(img, "sauvola")
    assert out.shape == img.shape
    assert set(np.unique(out)).issubset({0, 255})


def test_enhance_contrast_and_denoise_preserve_shape() -> None:
    img = _doc_image()
    assert enhance_contrast(img).shape == img.shape
    assert denoise(img, method="median").shape == img.shape


# ------------------------------- crop -------------------------------------- #
def test_auto_crop_trims_margins() -> None:
    img = np.full((400, 400), 255, dtype=np.uint8)
    img[150:250, 150:250] = 0  # nội dung ở giữa
    cropped, box = auto_crop(img, pad=5)
    assert box is not None
    assert cropped.shape[0] < img.shape[0] and cropped.shape[1] < img.shape[1]
    # Nội dung (pixel đen) vẫn còn sau khi cắt
    assert (cropped == 0).any()


def test_auto_crop_blank_image_returns_original() -> None:
    blank = np.full((200, 200), 255, dtype=np.uint8)
    out, box = auto_crop(blank)
    assert box is None
    assert out.shape == blank.shape


# ------------------------- Preprocessor end-to-end ------------------------- #
def test_preprocessor_on_image_array() -> None:
    page = PageImage(image=to_bgr(_doc_image()), page_index=0, dpi=200)
    cfg = PreprocessConfig(denoise=False, binarize="otsu")  # tắt denoise cho nhanh
    from ocr_idp.preprocess.pipeline_pre import Preprocessor

    out = Preprocessor(cfg).process_page(page)
    assert out.image.ndim == 2  # đã về ảnh xám/nhị phân
    assert "skew_angle" in out.preprocess_meta
    assert out.preprocess_meta.get("binarize") == "otsu"


def test_preprocessor_text_layer_skips_geometry() -> None:
    # Trang có text-layer -> bỏ deskew/crop, giữ hình học
    from ocr_idp.types import BBox, TextLayerLine

    page = PageImage(
        image=to_bgr(_doc_image()),
        page_index=0,
        dpi=200,
        text_layer=[TextLayerLine(text="Họ và tên", bbox=BBox(0, 0, 50, 10))],
    )
    from ocr_idp.preprocess.pipeline_pre import Preprocessor

    out = Preprocessor(PreprocessConfig()).process_page(page)
    assert out.preprocess_meta.get("geometry_skipped") is True
    assert "skew_angle" not in out.preprocess_meta


def test_load_image_file() -> None:
    # Dùng ảnh scan synthetic nếu đã sinh (M1); nếu chưa có thì bỏ qua
    sample = Path("data/synthetic/order_slip/sample_01_scan.png")
    if not sample.exists():
        pytest.skip("Chưa có dữ liệu synthetic (chạy: ocr-idp make-data)")
    from ocr_idp.preprocess.pdf_render import load_pages

    pages = load_pages(sample, target_dpi=150)
    assert len(pages) == 1 and pages[0].image.ndim == 3


def test_render_pdf_text_layer_if_fitz() -> None:
    pytest.importorskip("fitz")
    sample = Path("data/synthetic/account_opening_individual/sample_01.pdf")
    if not sample.exists():
        pytest.skip("Chưa có dữ liệu synthetic (chạy: ocr-idp make-data)")
    from ocr_idp.preprocess.pdf_render import load_pages

    pages = load_pages(sample, target_dpi=150, text_layer_min_chars=20)
    assert len(pages) >= 1
    assert pages[0].has_text_layer  # PDF synthetic luôn có text-layer
    assert any("TÀI KHOẢN" in ln.text.upper() for ln in pages[0].text_layer)

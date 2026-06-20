"""Test M3: registry engine, fast-path text-layer, và tích hợp Pipeline.ocr.

RapidOCR thật chỉ test khi đã cài (importorskip); phần còn lại dùng engine giả.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ocr_idp.config import OCRConfig, load_config
from ocr_idp.ocr.base import OCREngine
from ocr_idp.ocr.registry import available_engines, get_engine, register_engine
from ocr_idp.ocr.textlayer import ocr_result_from_text_layer
from ocr_idp.types import BBox, Line, OCRResult, PageImage, TextLayerLine


# ----- Engine giả để test registry & pipeline (không cần thư viện ngoài) ---- #
@register_engine
class _DummyEngine(OCREngine):
    name = "dummy_test"
    requires = ()

    def recognize(self, page: PageImage) -> OCRResult:
        return OCRResult(
            page_index=page.page_index,
            lines=[Line(text="xin chào", bbox=BBox(0, 0, 10, 10), confidence=0.9)],
            engine=self.name,
            image_width=page.width,
            image_height=page.height,
        )


def _blank_page(text_layer=None) -> PageImage:
    return PageImage(image=np.full((40, 60), 255, np.uint8), page_index=0, dpi=150, text_layer=text_layer)


# -------------------------------- registry --------------------------------- #
def test_registry_lists_rapidocr_and_dummy() -> None:
    engines = available_engines()
    assert "rapidocr" in engines  # engine mặc định luôn được đăng ký
    assert "dummy_test" in engines


def test_get_unknown_engine_raises() -> None:
    with pytest.raises(KeyError):
        get_engine("khong_ton_tai")


def test_get_dummy_engine_and_recognize() -> None:
    eng = get_engine("dummy_test", OCRConfig())
    res = eng.recognize(_blank_page())
    assert res.engine == "dummy_test"
    assert res.text == "xin chào"


def test_rapidocr_requires_deps_or_raises() -> None:
    # Nếu chưa cài rapidocr -> get_engine phải báo lỗi rõ ràng (RuntimeError)
    from ocr_idp.ocr.rapidocr_engine import RapidOCREngine

    if not RapidOCREngine.is_available():
        with pytest.raises(RuntimeError):
            get_engine("rapidocr")


# ----------------------------- text-layer ---------------------------------- #
def test_text_layer_conversion() -> None:
    page = _blank_page(
        text_layer=[
            TextLayerLine(text="GIẤY ĐỀ NGHỊ", bbox=BBox(10, 5, 200, 20)),
            TextLayerLine(text="Họ và tên: Nguyễn Văn A", bbox=BBox(10, 30, 250, 45)),
        ]
    )
    res = ocr_result_from_text_layer(page)
    assert res.engine == "textlayer"
    assert len(res.lines) == 2
    assert "Nguyễn Văn A" in res.text
    assert all(ln.confidence == 1.0 for ln in res.lines)


# ----------------------------- Pipeline.ocr -------------------------------- #
def test_pipeline_ocr_prefers_text_layer() -> None:
    from ocr_idp.pipeline import Pipeline

    page = _blank_page(text_layer=[TextLayerLine(text="abc", bbox=BBox(0, 0, 10, 10))])
    results = Pipeline(load_config()).ocr([page])
    assert results[0].engine == "textlayer"  # không cần engine thật


def test_pipeline_ocr_uses_engine_when_no_text_layer() -> None:
    from ocr_idp.pipeline import Pipeline

    cfg = load_config(overrides={"ocr.engine": "dummy_test"})
    results = Pipeline(cfg).ocr([_blank_page()])
    assert results[0].engine == "dummy_test"


def test_overlay_draws_without_error() -> None:
    from ocr_idp.ocr.overlay import draw_ocr_overlay

    page = _blank_page()
    res = OCRResult(page_index=0, lines=[Line("x", BBox(1, 1, 20, 15), 0.9)], engine="dummy_test")
    canvas = draw_ocr_overlay(page.image, res)
    assert canvas.ndim == 3 and canvas.shape[:2] == page.image.shape


# -------------------- RapidOCR thật (chỉ khi đã cài) ----------------------- #
def test_rapidocr_smoke_if_installed() -> None:
    pytest.importorskip("rapidocr_onnxruntime")
    pytest.importorskip("onnxruntime")
    sample = Path("data/raw/form_7.pdf")  # PDF thật dạng scan -> phải OCR
    if not sample.exists():
        pytest.skip("Chưa có dữ liệu thật data/raw/form_7.pdf")

    from ocr_idp.pipeline import Pipeline

    pipe = Pipeline(load_config())
    pages = pipe.preprocess(sample)
    results = pipe.ocr(pages, use_text_layer=False)  # ép OCR mọi trang
    # OCR đọc được chữ trên trang scan + gắn đúng số trang vào từng dòng
    assert sum(len(r.lines) for r in results) > 0
    assert all(ln.page_index == r.page_index for r in results for ln in r.lines)


# ------------------------- VietOCR (kéo lên sớm) --------------------------- #
def test_vietocr_registered_and_unavailable_without_torch() -> None:
    from ocr_idp.ocr.registry import available_engines
    from ocr_idp.ocr.vietocr_engine import VietOCREngine

    assert "vietocr" in available_engines()
    # torch chưa có wheel cho host 3.14 -> không sẵn sàng -> get_engine báo lỗi rõ
    if not VietOCREngine.is_available():
        with pytest.raises(RuntimeError):
            get_engine("vietocr")


def test_vietocr_recognize_logic_with_mocks(monkeypatch) -> None:
    """Kiểm tra logic cắt vùng + ghép kết quả của VietOCR mà KHÔNG cần torch."""
    from ocr_idp.config import OCRConfig
    from ocr_idp.ocr.vietocr_engine import VietOCREngine

    engine = VietOCREngine(OCRConfig())

    class _FakeDetector:
        def detect(self, img):
            return [BBox(10, 10, 120, 30), BBox(10, 40, 260, 62)]

    class _FakePredictor:
        def predict(self, pil_img, return_prob=False):
            return ("Họ và tên", 0.97)

    engine._detector = _FakeDetector()
    monkeypatch.setattr(engine, "_get_predictor", lambda: _FakePredictor())

    page = PageImage(image=np.full((100, 300, 3), 255, np.uint8), page_index=0, dpi=150)
    res = engine.recognize(page)
    assert res.engine == "vietocr"
    assert len(res.lines) == 2
    assert all(ln.text == "Họ và tên" for ln in res.lines)
    assert all(abs(ln.confidence - 0.97) < 1e-6 for ln in res.lines)


def test_rapidocr_detector_real_if_installed() -> None:
    """Phần PHÁT HIỆN VÙNG của VietOCR (RapidOCR detector) chạy thật trên host."""
    pytest.importorskip("rapidocr_onnxruntime")
    sample = Path("data/raw/form_7.pdf")
    if not sample.exists():
        pytest.skip("Chưa có dữ liệu thật data/raw/form_7.pdf")

    from ocr_idp.ocr.detection import RapidOCRDetector
    from ocr_idp.preprocess.pdf_render import load_pages

    page = load_pages(sample, target_dpi=150)[0]
    boxes = RapidOCRDetector().detect(page.image)
    assert len(boxes) > 5  # trang biểu mẫu có nhiều dòng -> phát hiện được nhiều vùng

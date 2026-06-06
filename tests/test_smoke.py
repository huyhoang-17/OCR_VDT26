"""Smoke test cho khung M0: import sạch + cấu hình nạp được + types hoạt động.

Chỉ phụ thuộc deps nhẹ (pydantic, pyyaml) -> chạy được trên mọi môi trường.
"""

from __future__ import annotations

from ocr_idp import __version__
from ocr_idp.config import AppConfig, load_config
from ocr_idp.types import BBox, ExtractionResult, FieldValue, Line, OCRResult


def test_version() -> None:
    assert isinstance(__version__, str) and __version__


def test_load_default_config() -> None:
    cfg = load_config("configs/default.yaml")
    assert isinstance(cfg, AppConfig)
    assert cfg.ocr.engine == "rapidocr"
    assert cfg.preprocess.target_dpi == 300
    assert 0.0 <= cfg.validation.min_confidence <= 1.0


def test_config_defaults_without_file() -> None:
    # File không tồn tại -> dùng mặc định, không lỗi
    cfg = load_config("configs/__khong_ton_tai__.yaml")
    assert cfg.ocr.engine == "rapidocr"
    assert cfg.extraction.llm.enabled is False


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("OCRIDP_OCR_ENGINE", "tesseract")
    monkeypatch.setenv("OCRIDP_LOG_LEVEL", "DEBUG")
    cfg = load_config("configs/default.yaml")
    assert cfg.ocr.engine == "tesseract"
    assert cfg.log_level == "DEBUG"


def test_bbox_geometry() -> None:
    b = BBox(0, 0, 10, 20)
    assert b.width == 10 and b.height == 20
    assert b.area == 200
    assert (b.cx, b.cy) == (5, 10)


def test_bbox_iou() -> None:
    a = BBox(0, 0, 10, 10)
    b = BBox(0, 0, 10, 10)
    assert a.iou(b) == 1.0
    c = BBox(100, 100, 110, 110)
    assert a.iou(c) == 0.0
    # giao 1 nửa theo chiều ngang
    d = BBox(5, 0, 15, 10)
    assert abs(a.iou(d) - (50 / 150)) < 1e-9


def test_bbox_from_points() -> None:
    poly = [(2, 3), (12, 3), (12, 9), (2, 9)]
    b = BBox.from_points(poly)
    assert b.to_list() == [2, 3, 12, 9]


def test_ocrresult_text_and_conf() -> None:
    res = OCRResult(
        page_index=0,
        lines=[
            Line(text="Họ và tên", bbox=BBox(0, 0, 50, 10), confidence=0.9),
            Line(text="Nguyễn Văn A", bbox=BBox(0, 12, 80, 22), confidence=0.8),
        ],
        engine="dummy",
    )
    assert res.text == "Họ và tên\nNguyễn Văn A"
    assert abs(res.mean_confidence - 0.85) < 1e-9


def test_extraction_result_container() -> None:
    er = ExtractionResult(form_type="account_opening_individual")
    er.fields["full_name"] = FieldValue(name="full_name", raw_value="Nguyễn Văn A", value="Nguyễn Văn A", confidence=0.8)
    assert er.get("full_name").value == "Nguyễn Văn A"
    assert er.get("khong_co") is None

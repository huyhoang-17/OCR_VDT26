"""Test M8: 3 engine OCR mới (Tesseract/EasyOCR/Paddle) + benchmark.

Logic parse của từng engine được tách thành hàm tĩnh -> test KHÔNG cần cài
torch/paddle/tesseract-binary. Availability-gating test theo điều kiện cài đặt.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ocr_idp.config import OCRConfig, load_config
from ocr_idp.ocr.base import OCREngine
from ocr_idp.ocr.registry import available_engines, get_engine, register_engine
from ocr_idp.types import BBox, Line, OCRResult, PageImage


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


# ------------------------------- Benchmark --------------------------------- #
def test_discover_samples_pairs_scan_with_pdf() -> None:
    from ocr_idp.eval.benchmark import discover_samples

    pairs = discover_samples("data", limit=2)
    if not pairs:
        pytest.skip("Chưa có dữ liệu synthetic")
    for png, pdf in pairs:
        assert png.name.endswith("_scan.png") and pdf.suffix == ".pdf" and pdf.exists()


def test_similarity_and_reports() -> None:
    from ocr_idp.eval.benchmark import EngineStat, recommend_default, to_csv, to_markdown, _similarity

    assert _similarity("xin chao the gioi", "xin chao the gioi") == 100.0
    assert _similarity("xin chao", "hoan toan khac biet") < 100.0

    result = {
        "n_samples": 3, "records": [],
        "stats": [
            EngineStat("vietocr", True, 3, 500, 20, 0.95, 90, 88),
            EngineStat("rapidocr", True, 3, 120, 18, 0.90, 85, 40),
            EngineStat("easyocr", False, note="thiếu dependency"),
        ],
    }
    # vietocr thắng (sim có dấu cao nhất) -> đề xuất mặc định
    assert recommend_default(result) == "vietocr"
    md = to_markdown(result)
    assert "vietocr" in md and "Đề xuất engine mặc định" in md
    csv = to_csv(result)
    assert csv.splitlines()[0].startswith("engine,available") and "rapidocr" in csv


# Engine giả (nhẹ) để test toàn bộ đường benchmark mà không cần model nặng.
@register_engine
class _BenchDummy(OCREngine):
    name = "bench_dummy"
    requires = ()

    def recognize(self, page: PageImage) -> OCRResult:
        return OCRResult(
            page_index=page.page_index,
            lines=[Line("danh sach co dong", BBox(0, 0, 100, 12), 0.9)],
            engine=self.name, image_width=page.width, image_height=page.height,
            elapsed_ms=1.0,
        )


def test_benchmark_runs_end_to_end_with_dummy_engine() -> None:
    from ocr_idp.eval.benchmark import benchmark_engines, discover_samples

    if not discover_samples("data", limit=1):
        pytest.skip("Chưa có dữ liệu synthetic")
    result = benchmark_engines(engine_names=["bench_dummy"], config=load_config(), limit=1)
    assert result["n_samples"] == 1
    stat = result["stats"][0]
    assert stat.engine == "bench_dummy" and stat.available and stat.n_samples == 1
    assert len(result["records"]) == 1
    assert 0.0 <= stat.sim_unaccented <= 100.0

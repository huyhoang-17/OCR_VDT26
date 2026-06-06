"""Orchestrator nối các bước pipeline lại với nhau.

    PDF/Ảnh --[1]--> List[PageImage] --[2]--> List[OCRResult]
            --[3]--> Layout --[4]--> ExtractionResult --[5]--> JSON theo schema

Mỗi bước là một component độc lập, được nạp "lười" (lazy import) để:
  * khởi động/`--help` nhẹ, không kéo theo engine nặng;
  * dễ thay thế từng bước mà không ảnh hưởng phần còn lại.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .config import AppConfig, load_config
from .logging_conf import get_logger
from .types import ExtractionResult, OCRResult, PageImage

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Kết quả chạy pipeline cho 1 tài liệu (kèm artifacts trung gian để debug)."""

    source: str
    form_type: Optional[str]
    pages: list[PageImage] = field(default_factory=list)
    ocr_results: list[OCRResult] = field(default_factory=list)
    extraction: Optional[ExtractionResult] = None
    output_json: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)


class Pipeline:
    """Điểm vào chính: cấu hình -> chạy các bước -> JSON.

    Cách dùng:
        pipe = Pipeline(load_config())
        result = pipe.run("form.pdf", form_type="account_opening_individual")
        print(result.output_json)
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        # Các bước nặng được khởi tạo lười (chỉ khi thực sự cần).
        self._preprocessor = None
        self._ocr_engine = None

    # --------------------------------------------------------------------- #
    # Khởi tạo lười từng bước
    # --------------------------------------------------------------------- #
    def _get_preprocessor(self):
        if self._preprocessor is None:
            from .preprocess.pipeline_pre import Preprocessor

            self._preprocessor = Preprocessor(self.config.preprocess)
        return self._preprocessor

    def _get_ocr_engine(self):
        if self._ocr_engine is None:
            from .ocr.registry import get_engine

            self._ocr_engine = get_engine(self.config.ocr.engine, self.config.ocr)
        return self._ocr_engine

    # --------------------------------------------------------------------- #
    # Từng bước (có thể gọi riêng để debug/visualize)
    # --------------------------------------------------------------------- #
    def preprocess(self, input_path: str | Path) -> list[PageImage]:
        """[1] Nạp + tiền xử lý file -> danh sách trang đã làm sạch."""
        return self._get_preprocessor().process_file(input_path)

    def ocr(self, pages: list[PageImage], use_text_layer: bool = True) -> list[OCRResult]:
        """[2] OCR từng trang. Trang có text-layer -> dùng fast path (bỏ OCR).

        Engine OCR chỉ được khởi tạo khi THỰC SỰ cần (có trang phải OCR) -> PDF
        text-layer chạy được mà không cần cài engine.
        """
        from .ocr.textlayer import ocr_result_from_text_layer

        results: list[OCRResult] = []
        for page in pages:
            if use_text_layer and page.has_text_layer:
                results.append(ocr_result_from_text_layer(page))
            else:
                results.append(self._get_ocr_engine().recognize(page))
        return results

    # --------------------------------------------------------------------- #
    # API công khai
    # --------------------------------------------------------------------- #
    def run(
        self,
        input_path: str | Path,
        form_type: Optional[str] = None,
        use_text_layer: bool = True,
    ) -> PipelineResult:
        """Chạy toàn bộ pipeline trên 1 file PDF/ảnh -> JSON theo schema.

        Args:
            input_path: đường dẫn file PDF hoặc ảnh.
            form_type: loại biểu mẫu; None -> tự phát hiện theo từ khóa.
            use_text_layer: dùng fast path text-layer cho PDF khi có.
        """
        import time

        from .extract.base import ExtractionContext
        from .forms.base import detect_form, get_form, list_forms
        from .normalize.text import strip_accents

        timings: dict[str, float] = {}

        t0 = time.perf_counter()
        pages = self.preprocess(input_path)
        timings["preprocess_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        t0 = time.perf_counter()
        ocr_results = self.ocr(pages, use_text_layer=use_text_layer)
        timings["ocr_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        all_lines = [ln for res in ocr_results for ln in res.lines]

        # Xác định loại biểu mẫu (nếu chưa chỉ định)
        if form_type is None:
            utext = strip_accents("\n".join(ln.text for ln in all_lines)).lower()
            form_type = detect_form(utext)
            if form_type is None:
                raise ValueError(
                    "Không tự xác định được loại biểu mẫu. Hãy truyền form_type "
                    f"(các loại hỗ trợ: {list(list_forms())})."
                )
            logger.info("Tự nhận diện biểu mẫu: %s", form_type)

        plugin = get_form(form_type)

        t0 = time.perf_counter()
        context = ExtractionContext(lines=all_lines, config=self.config, pages=pages)
        extraction = plugin.extract(context, self.config)
        output_json = plugin.assemble(extraction)
        timings["extract_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # Bổ sung thông tin engine OCR đã dùng vào _meta
        engines_used = sorted({res.engine for res in ocr_results})
        output_json.setdefault("_meta", {})["ocr_engine"] = engines_used
        output_json["_meta"]["timings_ms"] = timings

        return PipelineResult(
            source=str(input_path),
            form_type=form_type,
            pages=pages,
            ocr_results=ocr_results,
            extraction=extraction,
            output_json=output_json,
            warnings=extraction.warnings,
            timings_ms=timings,
        )

"""Orchestrator nối các bước pipeline lại với nhau.

    PDF/Ảnh --[1]--> List[PageImage] --[2]--> List[OCRResult]
            --[3]--> Layout --[4]--> ExtractionResult --[5]--> JSON theo schema

Mỗi bước là một component độc lập, được nạp "lười" (lazy import) để:
  * khởi động/`--help` nhẹ, không kéo theo engine nặng;
  * dễ thay thế từng bước mà không ảnh hưởng phần còn lại.

GHI CHÚ MỐC PHÁT TRIỂN:
  * M0 (hiện tại): chỉ có khung + hợp đồng interface; `run()` chưa khả dụng.
  * M2: nối bước tiền xử lý. M3: nối OCR. M4: nối trích xuất tối thiểu (MVP).
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

    Cách dùng (khi đã hoàn thiện ở M4+):
        pipe = Pipeline(load_config())
        result = pipe.run("form.pdf", form_type="account_opening_individual")
        print(result.output_json)
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        # Các bước được khởi tạo lười ở những mốc tương ứng (giữ None ở M0).
        self._preprocessor = None  # M2
        self._ocr_engine = None  # M3
        self._layout = None  # M5
        self._extractor = None  # M4/M6

    # --------------------------------------------------------------------- #
    # API công khai
    # --------------------------------------------------------------------- #
    def run(
        self,
        input_path: str | Path,
        form_type: Optional[str] = None,
        save_artifacts: bool = False,
    ) -> PipelineResult:
        """Chạy toàn bộ pipeline trên 1 file PDF/ảnh.

        Args:
            input_path: đường dẫn file PDF hoặc ảnh.
            form_type: loại biểu mẫu (nếu None -> sẽ tự phát hiện ở M7).
            save_artifacts: lưu ảnh tiền xử lý / OCR overlay vào output_dir.
        """
        raise NotImplementedError(
            "Pipeline.run() sẽ được nối ở các mốc M2–M4. "
            "Hiện M0 mới dựng khung & hợp đồng interface."
        )

"""Orchestrator bước tiền xử lý: file -> danh sách `PageImage` đã làm sạch.

Thứ tự xử lý cho ảnh scan (mỗi bước bật/tắt theo cấu hình):
    xám -> giới hạn kích thước -> deskew -> CLAHE -> khử nhiễu -> binarize -> auto-crop

Với trang PDF có TEXT-LAYER: chỉ áp các bước KHÔNG đổi hình học (để giữ nguyên
tọa độ text-layer); bỏ deskew/crop/resize vì trang render từ vector vốn đã thẳng.
"""

from __future__ import annotations

from pathlib import Path

from ..config import PreprocessConfig
from ..logging_conf import get_logger
from ..types import PageImage
from .base import limit_size, to_gray
from .binarize import binarize, enhance_contrast
from .crop import auto_crop
from .denoise import denoise
from .deskew import deskew
from .pdf_render import load_pages

logger = get_logger(__name__)


class Preprocessor:
    """Áp pipeline tiền xử lý lên từng trang."""

    def __init__(self, config: PreprocessConfig | None = None) -> None:
        self.cfg = config or PreprocessConfig()

    def process_file(self, path: str | Path) -> list[PageImage]:
        pages = load_pages(path, self.cfg.target_dpi, self.cfg.text_layer_min_chars)
        out = [self.process_page(p) for p in pages]
        logger.info(
            "Tiền xử lý '%s': %d trang (text-layer: %d).",
            Path(path).name, len(out), sum(1 for p in out if p.has_text_layer),
        )
        return out

    def process_page(self, page: PageImage) -> PageImage:
        gray = to_gray(page.image)
        meta = dict(page.preprocess_meta)

        if page.has_text_layer:
            # Chỉ chỉnh giá trị điểm ảnh, KHÔNG đổi hình học -> tọa độ text-layer còn đúng
            out = enhance_contrast(gray) if self.cfg.enhance_contrast else gray
            meta.update(text_layer=True, geometry_skipped=True)
        else:
            out, scale = limit_size(gray, self.cfg.max_side)
            meta["resize_scale"] = scale
            if self.cfg.deskew:
                out, angle = deskew(out)
                meta["skew_angle"] = round(angle, 3)
            if self.cfg.enhance_contrast:
                out = enhance_contrast(out)
            if self.cfg.denoise:
                out = denoise(out)
            if self.cfg.binarize and self.cfg.binarize.lower() != "none":
                out = binarize(out, self.cfg.binarize)
                meta["binarize"] = self.cfg.binarize
            if self.cfg.auto_crop:
                out, box = auto_crop(out)
                meta["crop_box"] = box

        page.image = out
        page.preprocess_meta = meta
        return page


def preprocess_file(path: str | Path, config: PreprocessConfig | None = None) -> list[PageImage]:
    """Hàm tiện dụng: tiền xử lý 1 file với cấu hình cho trước."""
    return Preprocessor(config).process_file(path)

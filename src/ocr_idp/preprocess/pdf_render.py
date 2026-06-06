"""Nạp đầu vào (PDF hoặc ảnh) -> danh sách `PageImage`.

PDF: render từng trang -> ảnh bằng PyMuPDF (fitz) — KHÔNG cần poppler. Đồng thời
phát hiện text-layer: nếu trang có sẵn text chất lượng (>= ngưỡng ký tự) thì lấy
luôn text + tọa độ (đã quy đổi sang pixel theo DPI) để pipeline BỎ QUA OCR.
"""

from __future__ import annotations

from pathlib import Path

from ..types import BBox, PageImage, TextLayerLine
from .base import read_image_file

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def load_pages(
    path: str | Path, target_dpi: int = 300, text_layer_min_chars: int = 50
) -> list[PageImage]:
    """Nạp file PDF/ảnh thành danh sách trang."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return render_pdf(p, target_dpi, text_layer_min_chars)
    if suffix in IMAGE_SUFFIXES:
        return [PageImage(image=read_image_file(p), page_index=0, dpi=target_dpi, source=str(p))]
    raise ValueError(f"Định dạng không hỗ trợ: {suffix} ({p})")


def _extract_text_layer(page, scale: float, min_chars: int):
    """Lấy text-layer của 1 trang PDF (gom theo dòng), quy đổi tọa độ sang pixel.

    Trả về list[TextLayerLine] nếu trang có đủ text, ngược lại None.
    """
    full_text = page.get_text("text") or ""
    if len(full_text.strip()) < min_chars:
        return None

    # words: (x0, y0, x1, y1, "word", block_no, line_no, word_no) — tọa độ theo points
    words = page.get_text("words")
    if not words:
        return None

    groups: dict[tuple[int, int], list] = {}
    for x0, y0, x1, y1, text, block_no, line_no, _word_no in words:
        groups.setdefault((block_no, line_no), []).append((x0, y0, x1, y1, text))

    lines: list[TextLayerLine] = []
    for _key, items in groups.items():
        items.sort(key=lambda it: it[0])  # trái -> phải
        text = " ".join(it[4] for it in items).strip()
        if not text:
            continue
        x0 = min(it[0] for it in items) * scale
        y0 = min(it[1] for it in items) * scale
        x1 = max(it[2] for it in items) * scale
        y1 = max(it[3] for it in items) * scale
        lines.append(TextLayerLine(text=text, bbox=BBox(x0, y0, x1, y1)))
    return lines or None


def render_pdf(path: str | Path, target_dpi: int, text_layer_min_chars: int) -> list[PageImage]:
    """Render PDF -> ảnh BGR theo DPI, kèm text-layer (nếu có)."""
    import fitz  # PyMuPDF (import lười: chỉ cần khi xử lý PDF)
    import numpy as np

    scale = target_dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    pages: list[PageImage] = []

    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc):
            text_layer = _extract_text_layer(page, scale, text_layer_min_chars)

            pix = page.get_pixmap(matrix=matrix, alpha=False)
            buf = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            if pix.n == 1:
                import cv2

                bgr = cv2.cvtColor(buf, cv2.COLOR_GRAY2BGR)
            else:
                bgr = buf[:, :, ::-1].copy()  # RGB -> BGR

            pages.append(
                PageImage(
                    image=bgr,
                    page_index=i,
                    dpi=target_dpi,
                    source=str(path),
                    text_layer=text_layer,
                )
            )
    return pages

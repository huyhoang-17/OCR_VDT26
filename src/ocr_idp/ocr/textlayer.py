"""Fast path: dựng OCRResult trực tiếp từ text-layer của PDF (bỏ qua OCR).

Khi PDF đã có text-layer chất lượng, dùng luôn text + tọa độ sẵn có sẽ nhanh và
chính xác hơn nhiều so với OCR ảnh render.
"""

from __future__ import annotations

from ..types import Line, OCRResult, PageImage

ENGINE_NAME = "textlayer"


def ocr_result_from_text_layer(page: PageImage) -> OCRResult:
    """Chuyển `page.text_layer` thành OCRResult (confidence = 1.0)."""
    lines = [
        Line(text=tl.text, bbox=tl.bbox, confidence=1.0, page_index=page.page_index)
        for tl in (page.text_layer or [])
    ]
    lines.sort(key=lambda ln: (round(ln.bbox.y1 / 10.0), ln.bbox.x1))
    return OCRResult(
        page_index=page.page_index,
        lines=lines,
        engine=ENGINE_NAME,
        image_width=page.width,
        image_height=page.height,
        elapsed_ms=0.0,
    )

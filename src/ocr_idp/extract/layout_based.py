"""Trích xuất theo TỌA ĐỘ/vùng (layout-based).

Hai chế độ:
  * Vùng tuyệt đối: spec.options.region = [x1,y1,x2,y2] (tỉ lệ 0..1 theo kích thước
    trang) -> gom mọi dòng có tâm nằm trong vùng (không cần nhãn). Hữu ích cho biểu
    mẫu bố cục cố định, trường không có nhãn rõ.
  * Tương đối nhãn: có spec.anchor -> tìm nhãn rồi gom các dòng bên phải cùng hàng
    + vài dòng ngay dưới (gộp lại) — phù hợp trường nhiều dòng (vd địa chỉ dài).
"""

from __future__ import annotations

from typing import Optional

from ..config import AppConfig
from ..normalize.text import clean_spaces, norm_key
from ..types import BBox, FieldStatus, FieldValue, Line
from .base import ExtractionContext, FieldExtractor, FieldSpec, vertical_overlap_ratio


class LayoutBasedExtractor(FieldExtractor):
    strategy = "layout"

    def __init__(self, config: AppConfig) -> None:
        self.threshold = config.extraction.anchor.fuzzy_threshold

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        opts = spec.options or {}
        region = opts.get("region")
        if region:
            return self._extract_region(spec, ctx, region)
        if spec.anchor:
            return self._extract_relative(spec, ctx, max_below=int(opts.get("max_below", 1)))
        return FieldValue(name=spec.name, status=FieldStatus.MISSING, source="layout",
                          warnings=["layout cần 'region' hoặc 'anchor'"])

    # -- Vùng tuyệt đối ----------------------------------------------------- #
    def _extract_region(self, spec, ctx, region) -> FieldValue:
        if not ctx.pages:
            return FieldValue(name=spec.name, status=FieldStatus.MISSING, source="layout",
                              warnings=["thiếu ảnh trang cho vùng tuyệt đối"])
        page = ctx.pages[0]
        w, h = page.width or 1, page.height or 1
        x1, y1, x2, y2 = region[0] * w, region[1] * h, region[2] * w, region[3] * h
        sel = [ln for ln in ctx.lines if x1 <= ln.bbox.cx <= x2 and y1 <= ln.bbox.cy <= y2]
        return self._build(spec, sel)

    # -- Tương đối nhãn ----------------------------------------------------- #
    def _extract_relative(self, spec, ctx, max_below: int) -> FieldValue:
        from rapidfuzz import fuzz

        anchors = [norm_key(a) for a in spec.anchor]
        anchor_line = None
        best = -1.0
        for ln in ctx.lines:
            score = max(fuzz.ratio(a, norm_key(ln.text)) for a in anchors)
            if score >= self.threshold and score > best:
                best, anchor_line = score, ln
        if anchor_line is None:
            return FieldValue(name=spec.name, status=FieldStatus.MISSING, source="layout",
                              warnings=[f"không thấy nhãn {spec.anchor}"])

        ab = anchor_line.bbox
        sel = [
            ln for ln in ctx.lines
            if ln is not anchor_line
            and vertical_overlap_ratio(ln.bbox, ab) >= 0.4
            and ln.bbox.x1 >= ab.x2 - 0.5 * ab.height
        ]
        # Thêm vài dòng ngay dưới (cùng cột) cho trường nhiều dòng
        below = sorted(
            (ln for ln in ctx.lines
             if ln.bbox.y1 > ab.y2 - 0.2 * ab.height
             and (ln.bbox.y1 - ab.y2) < (max_below + 1) * ab.height
             and abs(ln.bbox.x1 - ab.x2) < 6 * ab.height),
            key=lambda ln: ln.bbox.y1,
        )[:max_below]
        return self._build(spec, sel + below)

    @staticmethod
    def _build(spec: FieldSpec, lines: list[Line]) -> FieldValue:
        lines = sorted(lines, key=lambda ln: (round(ln.bbox.y1 / 10.0), ln.bbox.x1))
        text = clean_spaces(" ".join(ln.text for ln in lines))
        if not text:
            return FieldValue(name=spec.name, status=FieldStatus.MISSING, source="layout",
                              warnings=["không có nội dung trong vùng"])
        conf = min((ln.confidence for ln in lines), default=0.0)
        bbox: Optional[BBox] = None
        if lines:
            bbox = BBox(min(l.bbox.x1 for l in lines), min(l.bbox.y1 for l in lines),
                        max(l.bbox.x2 for l in lines), max(l.bbox.y2 for l in lines))
        return FieldValue(name=spec.name, raw_value=text, confidence=conf, source="layout",
                          bbox=bbox, status=FieldStatus.OK)

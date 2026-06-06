"""Trích xuất theo nhãn (anchor/label) + fuzzy matching.

Quy trình:
  1. Tìm dòng khớp nhãn nhất (fuzz.ratio trên chuỗi đã bỏ dấu -> chạy cho cả
     text-layer có dấu lẫn ảnh scan mất dấu).
  2. Lấy giá trị: ưu tiên phần sau dấu ':' cùng dòng -> cùng hàng bên phải ->
     dòng ngay dưới.
  3. Duyệt các ứng viên nhãn theo điểm giảm dần, chọn ứng viên ĐẦU TIÊN có giá
     trị -> tránh nhầm nhãn trùng tên không có giá trị (vd nhãn "Email:" vs ô
     chọn "Email").
"""

from __future__ import annotations

from typing import Optional

from ..config import AppConfig
from ..normalize.text import clean_spaces, norm_key
from ..types import BBox, FieldStatus, FieldValue, Line
from .base import ExtractionContext, FieldExtractor, FieldSpec, find_value_below, find_value_right


class AnchorExtractor(FieldExtractor):
    strategy = "anchor"

    def __init__(self, config: AppConfig) -> None:
        self.threshold = config.extraction.anchor.fuzzy_threshold

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        from rapidfuzz import fuzz

        anchors = [norm_key(a) for a in spec.anchor] or [norm_key(spec.name)]

        scored: list[tuple[float, Line]] = []
        for ln in ctx.lines:
            key = norm_key(ln.text)
            if not key:
                continue
            score = max(fuzz.ratio(a, key) for a in anchors)
            if score >= self.threshold:
                scored.append((score, ln))
        scored.sort(key=lambda t: t[0], reverse=True)

        # Thử lần lượt các ứng viên nhãn tốt nhất, lấy cái đầu tiên ra được giá trị
        for score, anchor_line in scored[:5]:
            value = self._value_for(anchor_line, spec, ctx.lines)
            if value is not None:
                raw, bbox, conf = value
                return FieldValue(
                    name=spec.name,
                    raw_value=clean_spaces(raw),
                    confidence=float(conf),
                    source="anchor",
                    bbox=bbox,
                    status=FieldStatus.OK,
                )

        return FieldValue(
            name=spec.name,
            status=FieldStatus.MISSING,
            source="anchor",
            confidence=0.0,
            warnings=[f"không tìm thấy nhãn {spec.anchor or [spec.name]}"],
        )

    def _value_for(
        self, anchor_line: Line, spec: FieldSpec, lines: list[Line]
    ) -> Optional[tuple[str, Optional[BBox], float]]:
        """Lấy giá trị quanh dòng nhãn. Trả về (raw, bbox, confidence) hoặc None."""
        # 1) Giá trị nằm sau dấu ':' cùng dòng (nhãn + giá trị chung 1 box)
        if ":" in anchor_line.text:
            after = anchor_line.text.split(":", 1)[1].strip()
            if after:
                return after, anchor_line.bbox, anchor_line.confidence

        # 2) Cùng hàng, bên phải
        order = (find_value_right, find_value_below)
        if spec.value_direction == "below":
            order = (find_value_below, find_value_right)
        for finder in order:
            vline = finder(lines, anchor_line)
            if vline is not None and vline.text.strip():
                return vline.text, vline.bbox, vline.confidence
        return None

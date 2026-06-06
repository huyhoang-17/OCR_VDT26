"""Trích xuất trường RADIO (chọn 1) — vd chiều lệnh MUA/BÁN, sàn, loại lệnh, kênh.

Khác checkbox (chọn nhiều -> list): radio trả về MỘT giá trị (key lựa chọn được
tick). Tái dùng cơ chế phát hiện ô vuông của checkbox; trong nhóm, chọn ô có tỉ
lệ mực ở lõi cao nhất và vượt ngưỡng tick.
"""

from __future__ import annotations

from ..layout.checkbox import detect_checkbox_state
from ..preprocess.base import to_gray
from ..types import FieldStatus, FieldValue, Line
from .base import ExtractionContext, FieldExtractor, FieldSpec
from .layout_fields import _find_label_lines


class RadioExtractor(FieldExtractor):
    strategy = "radio"

    def __init__(self, tick_threshold: float = 0.05) -> None:
        self.tick_threshold = tick_threshold

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        image = ctx.pages[0].image if ctx.pages else None
        if image is None or not spec.options:
            return FieldValue(name=spec.name, value=None, status=FieldStatus.MISSING,
                              source="radio", warnings=["thiếu ảnh hoặc 'options'"])
        gray = to_gray(image)

        any_box = False
        best_key, best_ratio = None, -1.0
        for key, label in spec.options.items():
            ratio, found = self._best_box_ratio(gray, ctx.lines, label)
            if found:
                any_box = True
                if ratio > best_ratio:
                    best_ratio, best_key = ratio, key

        if not any_box:
            return FieldValue(name=spec.name, value=None, status=FieldStatus.MISSING,
                              source="radio", warnings=["không thấy ô chọn cạnh nhãn"])
        if best_ratio < self.tick_threshold:
            return FieldValue(name=spec.name, value=None, confidence=0.5, source="radio",
                              status=FieldStatus.OK, warnings=["không lựa chọn nào được tick"])
        return FieldValue(name=spec.name, value=best_key, raw_value=str(best_key),
                          confidence=0.75, source="radio", status=FieldStatus.OK)

    @staticmethod
    def _best_box_ratio(gray, lines: list[Line], label: str) -> tuple[float, bool]:
        """Tỉ lệ mực cao nhất trong các ô vuông tìm thấy cạnh nhãn `label`."""
        best_ratio, found_box = -1.0, False
        for ln in _find_label_lines(lines, label):
            _ticked, box, ratio = detect_checkbox_state(gray, ln.bbox)
            if box is not None:
                found_box = True
                if ratio > best_ratio:
                    best_ratio = ratio
        return best_ratio, found_box

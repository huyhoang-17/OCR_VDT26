"""Trích xuất trường dựa trên LAYOUT/hình ảnh: checkbox/radio và chữ ký.

Cần ảnh trang (ctx.pages), không chỉ text OCR. Để phân biệt nhãn trùng tên (vd
ô chọn "Email" vs nhãn "Email:" của địa chỉ email), ta chỉ coi là ô chọn khi
THỰC SỰ tìm thấy ô vuông cạnh nhãn.
"""

from __future__ import annotations

from typing import Optional

from ..layout.checkbox import detect_checkbox_state
from ..layout.signature import detect_signature
from ..normalize.text import norm_key
from ..preprocess.base import to_gray
from ..types import FieldStatus, FieldValue, Line
from .base import ExtractionContext, FieldExtractor, FieldSpec


def _find_label_lines(lines: list[Line], labels, threshold: int = 85) -> list[Line]:
    """Tất cả dòng khớp 1 trong các nhãn (sắp theo điểm giảm dần)."""
    from rapidfuzz import fuzz

    if isinstance(labels, str):
        labels = [labels]
    keys = [norm_key(la) for la in labels]
    scored = []
    for ln in lines:
        k = norm_key(ln.text)
        if not k:
            continue
        s = max(fuzz.ratio(key, k) for key in keys)
        if s >= threshold:
            scored.append((s, ln))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [ln for _s, ln in scored]


class CheckboxExtractor(FieldExtractor):
    strategy = "checkbox"

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        image = ctx.pages[0].image if ctx.pages else None
        if image is None or not spec.options:
            return FieldValue(name=spec.name, value=[], status=FieldStatus.MISSING,
                              source="checkbox", warnings=["thiếu ảnh hoặc 'options'"])
        gray = to_gray(image)
        selected: list[str] = []
        for key, label in spec.options.items():
            if self._option_ticked(gray, ctx.lines, label):
                selected.append(key)
        return FieldValue(
            name=spec.name, value=selected, raw_value=", ".join(selected),
            confidence=0.75, source="checkbox", status=FieldStatus.OK,
        )

    @staticmethod
    def _option_ticked(gray, lines: list[Line], label: str) -> bool:
        best_ratio, found_box = -1.0, False
        ticked = False
        for ln in _find_label_lines(lines, label):
            is_ticked, box, ratio = detect_checkbox_state(gray, ln.bbox)
            if box is not None:  # chỉ tin ứng viên thực sự có ô vuông cạnh nhãn
                found_box = True
                if ratio > best_ratio:
                    best_ratio, ticked = ratio, is_ticked
        return ticked if found_box else False


class SignatureExtractor(FieldExtractor):
    strategy = "signature"

    _DEFAULT_ANCHORS = ["Ký, ghi rõ họ tên", "Người đặt lệnh", "Nhà đầu tư", "Ký tên"]

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        image = ctx.pages[0].image if ctx.pages else None
        if image is None:
            return FieldValue(name=spec.name, value=None, status=FieldStatus.MISSING,
                              source="signature", warnings=["thiếu ảnh"])
        gray = to_gray(image)
        anchors = spec.anchor or self._DEFAULT_ANCHORS
        candidates = _find_label_lines(ctx.lines, anchors)
        if not candidates:
            return FieldValue(name=spec.name, value=False, confidence=0.5, source="signature",
                              status=FieldStatus.OK, warnings=["không thấy nhãn vùng ký"])
        present, ratio = detect_signature(gray, candidates[0].bbox)
        return FieldValue(
            name=spec.name, value=bool(present), raw_value=str(present),
            confidence=0.7, source="signature", status=FieldStatus.OK,
        )

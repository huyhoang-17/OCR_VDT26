"""Kiểm tra dữ liệu sau trích xuất+chuẩn hóa: gắn cờ trường cần người kiểm tra.

Quy tắc:
  * Trường bắt buộc mà rỗng  -> MISSING.
  * Trường có cảnh báo chuẩn hóa (sai định dạng) -> INVALID_FORMAT.
  * Trường confidence < ngưỡng -> LOW_CONFIDENCE.
Trạng thái MISSING đã có sẵn (vd checkbox/chữ ký hoãn M5) được giữ nguyên.
"""

from __future__ import annotations

from ..types import FieldStatus, FieldValue


def _is_empty(value) -> bool:
    return value is None or value == "" or value == []


def validate_fields(
    fields: dict[str, FieldValue], specs: list, min_confidence: float
) -> list[str]:
    """Cập nhật `.status` của từng FieldValue và trả về danh sách cảnh báo (toàn cục)."""
    spec_by_name = {s.name: s for s in specs}
    warnings: list[str] = []

    for name, fv in fields.items():
        spec = spec_by_name.get(name)
        required = bool(spec and spec.required)
        threshold = (spec.min_confidence if spec and spec.min_confidence else min_confidence)

        # 1) Bắt buộc nhưng rỗng
        if required and _is_empty(fv.value):
            fv.status = FieldStatus.MISSING
            warnings.append(f"[{name}] thiếu giá trị (bắt buộc)")
            continue

        # 2) Cảnh báo từ trích xuất/chuẩn hóa -> sai định dạng (giữ MISSING nếu đã có)
        if fv.warnings:
            if fv.status == FieldStatus.OK:
                fv.status = FieldStatus.INVALID_FORMAT
            warnings.extend(f"[{name}] {w}" for w in fv.warnings)

        # 3) Confidence thấp
        if not _is_empty(fv.value) and 0.0 < fv.confidence < threshold:
            if fv.status == FieldStatus.OK:
                fv.status = FieldStatus.LOW_CONFIDENCE
            warnings.append(f"[{name}] độ tin cậy thấp ({fv.confidence:.2f} < {threshold:.2f})")

    return warnings

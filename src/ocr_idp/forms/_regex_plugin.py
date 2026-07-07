"""Base dùng chung cho các extractor eform theo **bảng RULES** (regex trên text).

Mỗi eform chuyên biệt chỉ cần khai báo `form_type`, `title`, `classify_keywords`
và `RULES` — không lặp lại logic quét/chuẩn hóa. Dựng JSON qua `assemble` mặc
định của `FormPlugin` (lồng theo dot-path): tên trường `results.<KEY>`.

Mỗi RULE = (result_key, kind, pattern[, options]) với `kind`:
  * ``text``   — group(1), gộp khoảng trắng.
  * ``date``   — group(1,2,3) = ngày/tháng/năm → ISO ``YYYY-MM-DDT00:00:00+00:00``.
  * ``date_dmy`` — group(1,2,3) = ngày/tháng/năm → chuỗi ``DD/MM/YYYY`` (một số
                 eform lưu ngày dạng chuỗi dd/mm/yyyy thay vì ISO).
  * ``digits`` — group(1), chỉ giữ chữ số (giữ dạng chuỗi, kể cả số 0 đầu).
  * ``dong``   — như ``digits`` + hậu tố `" đồng"`.
  * ``phone``  — như ``digits`` (số điện thoại).
  * ``choice`` — group(1) map về 1 giá trị chuẩn trong ``options`` (bỏ dấu khi so)
                 → khớp được cả khi OCR mất dấu tiếng Việt.

Ghi chú về scan: các PDF eform (trừ eform1) là ảnh scan; RapidOCR trên host MẤT
dấu tiếng Việt → trường text tự do khó khớp exact (cần VietOCR/Docker). ``choice``
map về giá trị chuẩn nên vẫn khớp; số/ngày/mã đọc tốt.
"""

from __future__ import annotations

import re
from typing import Any

from ..config import AppConfig
from ..extract.base import ExtractionContext
from ..normalize.apply import normalize_choice
from ..normalize.text import clean_spaces
from ..types import ExtractionResult, FieldStatus, FieldValue
from .base import FormPlugin

_ZERO_WIDTH = re.compile(r"[​‌‍﻿­]")


def iso_date(day: Any, month: Any, year: Any) -> str:
    """(ngày, tháng, năm) → ISO 8601 nửa đêm UTC theo định dạng ground-truth."""
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}T00:00:00+00:00"


class RegexFormPlugin(FormPlugin):
    """Extractor eform theo bảng RULES (xem docstring module)."""

    STATUS: str = "DONE"          # giá trị trường top-level `status`
    RULES: list[tuple] = []       # (result_key, kind, pattern[, options])

    def field_specs(self):  # type: ignore[override]
        return []

    def extract(self, context: ExtractionContext, config: AppConfig) -> ExtractionResult:
        flat = clean_spaces(_ZERO_WIDTH.sub("", "\n".join(ln.text for ln in context.lines)))
        fields: dict[str, FieldValue] = {}

        def put(name: str, value: Any) -> None:
            fields[name] = FieldValue(
                name=name, raw_value=str(value), value=value,
                confidence=0.9, source="rule", status=FieldStatus.OK,
            )

        put("status", self.STATUS)
        put("form_id", self.form_type)

        for rule in self.RULES:
            key, kind, pattern = rule[0], rule[1], rule[2]
            m = re.search(pattern, flat)
            if not m:
                continue
            if kind == "date":
                value: Any = iso_date(m.group(1), m.group(2), m.group(3))
            elif kind == "date_dmy":
                value = f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{int(m.group(3)):04d}"
            elif kind in ("digits", "phone"):
                value = re.sub(r"\D", "", m.group(1))
            elif kind == "dong":
                value = re.sub(r"\D", "", m.group(1)) + " đồng"
            elif kind == "choice":
                value, _ = normalize_choice(m.group(1), rule[3])
            else:  # text
                value = clean_spaces(m.group(1))
            put(f"results.{key}", value)

        return ExtractionResult(form_type=self.form_type, fields=fields, warnings=[])

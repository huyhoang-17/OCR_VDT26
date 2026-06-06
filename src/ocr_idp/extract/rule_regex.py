"""Trích xuất bằng regex trên toàn bộ text của trang (không cần nhãn cố định).

Chạy regex trên text ĐÃ BỎ DẤU trước (ổn cho cả scan), sau đó thử text gốc. Hữu
ích cho trường không có nhãn rõ (vd 'ngày ... tháng ... năm ...' của ngày đăng ký).
"""

from __future__ import annotations

import re
from typing import Optional

from ..config import AppConfig
from ..normalize.text import clean_spaces, strip_accents
from ..types import FieldStatus, FieldValue, Line
from .base import ExtractionContext, FieldExtractor, FieldSpec


class RuleExtractor(FieldExtractor):
    strategy = "rule"

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        if not spec.regex:
            return FieldValue(name=spec.name, status=FieldStatus.MISSING, source="rule",
                              warnings=["strategy 'rule' nhưng thiếu 'regex'"])

        pattern = re.compile(spec.regex, re.IGNORECASE)
        match = pattern.search(ctx.text_unaccented) or pattern.search(ctx.text)
        if not match:
            return FieldValue(name=spec.name, status=FieldStatus.MISSING, source="rule",
                              confidence=0.0, warnings=[f"regex không khớp: {spec.regex}"])

        raw = match.group(1) if match.groups() else match.group(0)
        line = self._line_containing(ctx.lines, match.group(0))
        return FieldValue(
            name=spec.name,
            raw_value=clean_spaces(raw),
            confidence=line.confidence if line else 0.8,
            source="rule",
            bbox=line.bbox if line else None,
            status=FieldStatus.OK,
        )

    @staticmethod
    def _line_containing(lines: list[Line], needle: str) -> Optional[Line]:
        key = strip_accents(needle).lower()
        for ln in lines:
            if key in strip_accents(ln.text).lower():
                return ln
        return None

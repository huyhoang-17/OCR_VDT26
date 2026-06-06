"""Extractor 'tạm hoãn' cho các chiến lược chưa hiện thực ở mốc hiện tại.

Trả về FieldValue trạng thái MISSING kèm cảnh báo nêu rõ sẽ hỗ trợ ở mốc nào,
để JSON đầu ra vẫn đầy đủ cấu trúc và người dùng biết trường cần bổ sung sau.
"""

from __future__ import annotations

from typing import Any

from ..types import FieldStatus, FieldValue
from .base import ExtractionContext, FieldExtractor, FieldSpec


class DeferredExtractor(FieldExtractor):
    def __init__(self, strategy: str, milestone: str, default: Any = None) -> None:
        self.strategy = strategy
        self.milestone = milestone
        self.default = default

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        default = self.default() if callable(self.default) else self.default
        return FieldValue(
            name=spec.name,
            value=default,
            status=FieldStatus.MISSING,
            source=self.strategy,
            confidence=0.0,
            warnings=[f"chiến lược '{self.strategy}' sẽ hỗ trợ ở mốc {self.milestone}"],
        )

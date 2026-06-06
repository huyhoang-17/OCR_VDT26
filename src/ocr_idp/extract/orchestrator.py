"""Điều phối trích xuất: chọn extractor theo `strategy` của từng trường."""

from __future__ import annotations

from ..config import AppConfig
from ..types import FieldStatus, FieldValue
from .anchor_label import AnchorExtractor
from .base import ExtractionContext, FieldExtractor, FieldSpec
from .placeholders import DeferredExtractor
from .rule_regex import RuleExtractor


class ExtractionOrchestrator:
    """Map strategy -> extractor và chạy cho danh sách FieldSpec."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._extractors: dict[str, FieldExtractor] = {
            "anchor": AnchorExtractor(config),
            "rule": RuleExtractor(config),
            # Các chiến lược dưới đây sẽ hiện thực ở mốc sau (M5/M6):
            "checkbox": DeferredExtractor("checkbox", "M5", default=list),
            "signature": DeferredExtractor("signature", "M5", default=None),
            "layout": DeferredExtractor("layout", "M5/M6", default=None),
            "llm": DeferredExtractor("llm", "M6", default=None),
        }

    def extract_fields(
        self, specs: list[FieldSpec], context: ExtractionContext
    ) -> dict[str, FieldValue]:
        out: dict[str, FieldValue] = {}
        for spec in specs:
            extractor = self._extractors.get(spec.strategy)
            if extractor is None:
                out[spec.name] = FieldValue(
                    name=spec.name, status=FieldStatus.MISSING,
                    warnings=[f"strategy không hợp lệ: '{spec.strategy}'"],
                )
            else:
                out[spec.name] = extractor.extract(spec, context)
        return out

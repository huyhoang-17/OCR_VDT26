"""Điều phối trích xuất: chọn extractor theo `strategy` của từng trường."""

from __future__ import annotations

from ..config import AppConfig
from ..types import FieldStatus, FieldValue
from .anchor_label import AnchorExtractor
from .base import ExtractionContext, FieldExtractor, FieldSpec
from .layout_fields import CheckboxExtractor, SignatureExtractor
from .placeholders import DeferredExtractor
from .rule_regex import RuleExtractor


class ExtractionOrchestrator:
    """Map strategy -> extractor và chạy cho danh sách FieldSpec."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._extractors: dict[str, FieldExtractor] = {
            "anchor": AnchorExtractor(config),
            "rule": RuleExtractor(config),
            "checkbox": CheckboxExtractor(),  # M5
            "signature": SignatureExtractor(),  # M5
            # Các chiến lược dưới đây sẽ hiện thực ở mốc sau:
            "layout": DeferredExtractor("layout", "M6", default=None),
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

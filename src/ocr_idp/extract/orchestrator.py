"""Điều phối trích xuất: chọn extractor theo `strategy` của từng trường."""

from __future__ import annotations

from ..config import AppConfig
from ..types import FieldStatus, FieldValue
from ..types import FieldValue
from .anchor_label import AnchorExtractor
from .base import ExtractionContext, FieldExtractor, FieldSpec
from .layout_based import LayoutBasedExtractor
from .layout_fields import CheckboxExtractor, SignatureExtractor
from .rule_regex import RuleExtractor


class _LLMFallbackExtractor(FieldExtractor):
    """Base cho field strategy='llm' khi chạy không có LLM: dùng anchor/rule.

    Lời gọi LLM thật (nếu khả dụng) được FormPlugin thực hiện ở bước sau và GHI ĐÈ.
    """

    strategy = "llm"

    def __init__(self, config: AppConfig) -> None:
        self._anchor = AnchorExtractor(config)
        self._rule = RuleExtractor(config)

    def extract(self, spec: FieldSpec, ctx: ExtractionContext) -> FieldValue:
        if spec.anchor:
            return self._anchor.extract(spec, ctx)
        if spec.regex:
            return self._rule.extract(spec, ctx)
        from ..types import FieldStatus

        return FieldValue(name=spec.name, status=FieldStatus.MISSING, source="llm",
                          warnings=["strategy 'llm' nhưng thiếu LLM/anchor/regex"])


class ExtractionOrchestrator:
    """Map strategy -> extractor và chạy cho danh sách FieldSpec."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._extractors: dict[str, FieldExtractor] = {
            "anchor": AnchorExtractor(config),
            "rule": RuleExtractor(config),
            "checkbox": CheckboxExtractor(),  # M5
            "signature": SignatureExtractor(),  # M5
            "layout": LayoutBasedExtractor(config),  # M6
            "llm": _LLMFallbackExtractor(config),  # M6: base; LLM thật ở FormPlugin
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

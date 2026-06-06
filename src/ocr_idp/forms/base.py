"""Hệ thống plugin biểu mẫu: mỗi loại = schema + extraction.yaml + lớp plugin.

Thêm biểu mẫu mới = tạo thư mục con (schema.json + extraction.yaml + plugin.py
đăng ký qua @register_form) -> KHÔNG sửa core.
"""

from __future__ import annotations

import inspect
import json
from abc import ABC
from pathlib import Path
from typing import Any, Optional

import yaml

from ..config import AppConfig
from ..extract.base import ExtractionContext, FieldSpec
from ..extract.orchestrator import ExtractionOrchestrator
from ..normalize.apply import apply_normalization
from ..normalize.text import strip_accents
from ..types import ExtractionResult
from ..validate.validators import validate_fields

# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
_FORMS: dict[str, "FormPlugin"] = {}


def register_form(cls: type["FormPlugin"]) -> type["FormPlugin"]:
    """Decorator: khởi tạo & đăng ký 1 plugin biểu mẫu."""
    instance = cls()
    _FORMS[instance.form_type] = instance
    return cls


def _ensure_loaded() -> None:
    """Import các module plugin để decorator chạy."""
    from .account_opening import plugin  # noqa: F401  (Form A — M4)
    from .order_slip import plugin as _b  # noqa: F401  (Form B — M7)
    from .shareholder_list import plugin as _c  # noqa: F401  (Form C — M7)


def list_forms() -> dict[str, str]:
    _ensure_loaded()
    return {ft: p.title for ft, p in sorted(_FORMS.items())}


def get_form(form_type: str) -> "FormPlugin":
    _ensure_loaded()
    if form_type not in _FORMS:
        raise KeyError(f"Biểu mẫu không hỗ trợ: '{form_type}'. Hiện có: {sorted(_FORMS)}")
    return _FORMS[form_type]


def detect_form(text_unaccented: str, min_score: float = 0.34) -> Optional[str]:
    """Tự đoán loại biểu mẫu từ text (đã bỏ dấu) qua từ khóa. None nếu không chắc."""
    _ensure_loaded()
    best_type, best_score = None, 0.0
    for ft, plugin in _FORMS.items():
        score = plugin.classify(text_unaccented)
        if score > best_score:
            best_type, best_score = ft, score
    return best_type if best_score >= min_score else None


# --------------------------------------------------------------------------- #
# Base plugin
# --------------------------------------------------------------------------- #
class FormPlugin(ABC):
    """Lớp cơ sở cho plugin biểu mẫu. Tải schema/extraction từ cùng thư mục."""

    form_type: str = ""
    title: str = ""
    classify_keywords: list[str] = []  # từ khóa (không dấu, thường) để tự nhận diện

    def __init__(self) -> None:
        self._specs: Optional[list[FieldSpec]] = None
        self._schema: Optional[dict] = None

    # -- Tài nguyên đi kèm -------------------------------------------------- #
    def _dir(self) -> Path:
        return Path(inspect.getfile(self.__class__)).resolve().parent

    def load_schema(self) -> dict:
        if self._schema is None:
            self._schema = json.loads((self._dir() / "schema.json").read_text(encoding="utf-8"))
        return self._schema

    def field_specs(self) -> list[FieldSpec]:
        if self._specs is None:
            data = yaml.safe_load((self._dir() / "extraction.yaml").read_text(encoding="utf-8"))
            self._specs = [FieldSpec.from_dict(d) for d in (data.get("fields") or [])]
        return self._specs

    # -- Nhận diện ---------------------------------------------------------- #
    def classify(self, text_unaccented: str) -> float:
        """Tỉ lệ từ khóa nhận diện xuất hiện trong text (fuzzy -> chịu được lỗi OCR)."""
        if not self.classify_keywords:
            return 0.0
        from rapidfuzz import fuzz

        t = text_unaccented.lower()
        hits = sum(1 for kw in self.classify_keywords if fuzz.partial_ratio(kw, t) >= 85)
        return hits / len(self.classify_keywords)

    # -- Trích xuất --------------------------------------------------------- #
    def extract(self, context: ExtractionContext, config: AppConfig) -> ExtractionResult:
        specs = self.field_specs()
        fields = ExtractionOrchestrator(config).extract_fields(specs, context)
        apply_normalization(fields, specs)
        self._maybe_llm(specs, fields, context, config)
        warnings = validate_fields(fields, specs, config.validation.min_confidence)
        return ExtractionResult(form_type=self.form_type, fields=fields, warnings=warnings)

    def _maybe_llm(self, specs, fields, context, config: AppConfig) -> None:
        """Bước LLM (tùy chọn): trích field strategy='llm' và/hoặc SỬA trường yếu.

        Bỏ qua nếu không bật và không có field 'llm'; hoặc nếu LLM không khả dụng
        (thiếu key/thư viện) -> giữ kết quả rule/anchor (fallback).
        """
        from ..extract.llm_claude import ClaudeExtractor, is_llm_available
        from ..normalize.apply import apply_normalization as _apply
        from ..types import FieldStatus, FieldValue

        llm = config.extraction.llm
        explicit = [s for s in specs if s.strategy == "llm"]
        if not (llm.enabled or explicit):
            return
        if not is_llm_available(config):
            for s in explicit:
                fv = fields.get(s.name)
                if fv is not None:
                    fv.warnings.append("LLM không khả dụng (thiếu ANTHROPIC_API_KEY) — dùng rule/anchor")
            return

        # Chọn trường cần LLM: field 'llm' luôn có; nếu repair thì thêm field text yếu
        targets = list(explicit)
        if llm.enabled and llm.repair:
            min_conf = config.validation.min_confidence
            for s in specs:
                if s.strategy in ("anchor", "rule", "layout") and s not in targets:
                    fv = fields.get(s.name)
                    weak = fv is None or fv.value in (None, "", []) or fv.confidence < min_conf
                    if weak:
                        targets.append(s)
        if not targets:
            return

        values = ClaudeExtractor(config).extract(targets, context.text)
        changed = False
        for s in targets:
            val = values.get(s.name)
            if val is not None and val != "":
                fields[s.name] = FieldValue(
                    name=s.name, raw_value=str(val), confidence=0.9,
                    source="llm", status=FieldStatus.OK,
                )
                changed = True
        if changed:
            _apply(fields, specs)  # chuẩn hóa lại các giá trị LLM trả về

    # -- Dựng JSON cuối cùng ------------------------------------------------ #
    def assemble(self, extraction: ExtractionResult) -> dict[str, Any]:
        """Dựng JSON lồng nhau theo dot-path tên trường + khối _meta."""
        out: dict[str, Any] = {"form_type": self.form_type}
        confidence: dict[str, float] = {}
        status: dict[str, str] = {}
        for name, fv in extraction.fields.items():
            _set_dotpath(out, name, fv.value)
            confidence[name] = round(fv.confidence, 3)
            status[name] = fv.status.value
        out["_meta"] = {
            "confidence": confidence,
            "field_status": status,
            "warnings": extraction.warnings,
        }
        return out


def _set_dotpath(d: dict, dotted: str, value: Any) -> None:
    keys = dotted.split(".")
    cur = d
    for k in keys[:-1]:
        nxt = cur.get(k)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[k] = nxt
        cur = nxt
    cur[keys[-1]] = value

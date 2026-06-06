"""Trích xuất bằng Claude với structured JSON output (constrained).

Dùng `output_config.format` (json_schema) để BẢO ĐẢM JSON hợp lệ đúng schema. Rất
hợp để: trích trường khó, và đặc biệt SỬA LỖI DẤU tiếng Việt mà OCR scan làm mất
("Pham Van Hung" -> "Phạm Văn Hùng").

An toàn:
  * Mặc định TẮT; chỉ chạy khi `extraction.llm.enabled` (hoặc field strategy="llm")
    VÀ có ANTHROPIC_API_KEY.
  * Thiếu key/thư viện hoặc lỗi gọi API -> trả {} (pipeline tự fallback rule/anchor).
  * KHÔNG gửi temperature/budget_tokens (Opus 4.8/4.7 trả 400).
"""

from __future__ import annotations

import importlib.util
import json
import os

from ..config import AppConfig
from ..logging_conf import get_logger

logger = get_logger(__name__)

_SYSTEM = (
    "Bạn trích xuất trường dữ liệu từ văn bản OCR của biểu mẫu chứng khoán Việt Nam. "
    "Văn bản OCR có thể sai hoặc MẤT DẤU tiếng Việt — hãy khôi phục đúng chính tả có dấu. "
    "Ngày trả về dạng YYYY-MM-DD. Số trả về dạng số nguyên (không dấu phân tách). "
    "Nếu một trường không xuất hiện trong văn bản, trả về null. "
    "Chỉ dùng thông tin có trong văn bản, không bịa."
)


def is_llm_available(config: AppConfig) -> bool:
    """True nếu đã cài `anthropic` VÀ có API key trong môi trường."""
    if importlib.util.find_spec("anthropic") is None:
        return False
    return bool(os.environ.get(config.extraction.llm.api_key_env))


def _json_type_for(spec) -> dict:
    if getattr(spec, "choices", None):
        return {"enum": list(spec.choices) + [None]}
    if spec.normalizer in ("int", "money"):
        return {"type": ["integer", "null"]}
    return {"type": ["string", "null"]}


def build_schema(specs: list) -> dict:
    """Dựng JSON schema phẳng cho các trường cần trích (key = dot-path tên trường)."""
    props, required = {}, []
    for s in specs:
        t = _json_type_for(s)
        t["description"] = s.anchor[0] if s.anchor else s.name
        props[s.name] = t
        required.append(s.name)
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


def _user_prompt(ocr_text: str, specs: list) -> str:
    fields = "\n".join(f"- {s.name}: {(s.anchor[0] if s.anchor else s.name)}" for s in specs)
    return (
        "VĂN BẢN OCR:\n---\n" + ocr_text + "\n---\n\n"
        "Trích xuất các trường sau (đúng JSON schema được yêu cầu):\n" + fields
    )


class ClaudeExtractor:
    """Bọc 1 lời gọi Claude trả JSON theo schema cho 1 tập trường."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()  # đọc ANTHROPIC_API_KEY từ env
        return self._client

    def extract(self, specs: list, ocr_text: str) -> dict:
        """Trả về {field_name: value}. {} nếu lỗi/không trích được."""
        if not specs:
            return {}
        llm = self.config.extraction.llm
        schema = build_schema(specs)
        try:
            resp = self._get_client().messages.create(
                model=llm.model,
                max_tokens=llm.max_tokens,
                system=_SYSTEM,
                messages=[{"role": "user", "content": _user_prompt(ocr_text, specs)}],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
            text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
            data = json.loads(text) if text else {}
            return data if isinstance(data, dict) else {}
        except Exception as exc:  # noqa: BLE001 - mọi lỗi -> fallback êm
            logger.warning("Trích xuất LLM thất bại (%s) — fallback rule/anchor.", exc)
            return {}

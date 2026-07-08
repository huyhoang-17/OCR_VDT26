"""Tóm tắt tuân thủ: deterministic mặc định, OpenAI/Gemini là lớp diễn đạt."""

from __future__ import annotations

import importlib.util
import json
import os
from typing import Any

from ..logging_conf import get_logger
from .models import CheckStatus, ComplianceReport

logger = get_logger(__name__)

_SYSTEM = (
    "Bạn là chuyên viên viết biên bản tuân thủ bằng tiếng Việt. "
    "Dữ liệu đầu vào là kết quả đã được mã lệnh tính toán tất định. "
    "Chỉ diễn giải đúng các trạng thái, số liệu actual/expected và thông điệp được cung cấp; "
    "không tự tính lại, không thêm căn cứ pháp lý, dữ kiện hay vi phạm không có trong JSON. "
    "Viết 1-3 đoạn ngắn, nêu kết luận chung rồi ưu tiên lỗi trước cảnh báo."
)


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError):
        return False


def deterministic_summary(report: ComplianceReport) -> str:
    if not report.checks:
        return f"Chưa có luật nghiệp vụ liên-trường áp dụng cho {report.form_type}."
    counts = report.counts
    head = (
        f"Đã thực hiện {len(report.checks)} kiểm tra nghiệp vụ cho {report.form_type}: "
        f"{counts['pass']} đạt, {counts['violation']} vi phạm và {counts['skipped']} chưa đánh giá."
    )
    violations = [c for c in report.checks if c.status == CheckStatus.VIOLATION]
    if not violations:
        return head + " Không phát hiện vi phạm nghiệp vụ liên-trường."
    details = " ".join(
        f"[{c.severity.value.upper()}] {c.message}" for c in violations[:6]
    )
    if len(violations) > 6:
        details += f" Còn {len(violations) - 6} vi phạm khác trong bảng chi tiết."
    return head + " " + details


class ComplianceSummarizer:
    """Adapter LLM có fallback êm; payload không chứa JSON nguồn."""

    def summarize(
        self,
        report: ComplianceReport,
        provider: str = "deterministic",
        model: str | None = None,
        max_output_tokens: int = 700,
        api_key_env: str | None = None,
    ) -> ComplianceReport:
        provider = provider.lower().strip()
        fallback = deterministic_summary(report)
        if provider in ("", "none", "deterministic"):
            report.summary, report.summary_source = fallback, "deterministic"
            return report
        if provider not in ("openai", "gemini"):
            raise ValueError(f"Provider tóm tắt không hỗ trợ: {provider}")
        try:
            if provider == "openai":
                text = self._openai(
                    report.llm_payload(), model or "gpt-5.4-mini",
                    api_key_env or "OPENAI_API_KEY", max_output_tokens,
                )
            elif provider == "gemini":
                text = self._gemini(
                    report.llm_payload(), model or "gemini-3-flash-preview",
                    api_key_env or "GEMINI_API_KEY", max_output_tokens,
                )
            if not text.strip():
                raise RuntimeError("LLM trả về nội dung rỗng")
            report.summary, report.summary_source = text.strip(), provider
        except Exception as exc:  # noqa: BLE001 - LLM không được làm hỏng report
            logger.warning("Tóm tắt %s thất bại, dùng bản deterministic: %s", provider, exc)
            report.summary, report.summary_source = fallback, "deterministic_fallback"
            report.warnings.append(f"Không tạo được tóm tắt {provider}: {exc}")
        return report

    @staticmethod
    def _prompt(payload: dict[str, Any]) -> str:
        return "Hãy diễn giải kết quả kiểm tra sau:\n" + json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        )

    def _openai(self, payload: dict[str, Any], model: str, key_env: str, max_tokens: int) -> str:
        if not _module_available("openai"):
            raise RuntimeError("thiếu package openai")
        key = os.environ.get(key_env)
        if not key:
            raise RuntimeError(f"thiếu biến môi trường {key_env}")
        from openai import OpenAI

        response = OpenAI(api_key=key).responses.create(
            model=model,
            instructions=_SYSTEM,
            input=self._prompt(payload),
            max_output_tokens=max_tokens,
        )
        return str(response.output_text or "")

    def _gemini(self, payload: dict[str, Any], model: str, key_env: str, max_tokens: int) -> str:
        if not _module_available("google.genai"):
            raise RuntimeError("thiếu package google-genai")
        key = os.environ.get(key_env)
        if not key:
            raise RuntimeError(f"thiếu biến môi trường {key_env}")
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=self._prompt(payload),
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM,
                max_output_tokens=max_tokens,
            ),
        )
        return str(response.text or "")

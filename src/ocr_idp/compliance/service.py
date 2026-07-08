"""Facade dùng chung cho CLI, REST API và Streamlit."""

from __future__ import annotations

from typing import Any

from ..config import AppConfig, load_config
from .engine import ComplianceEngine
from .models import ComplianceReport
from .summary import ComplianceSummarizer


def build_compliance_report(
    document: dict[str, Any],
    config: AppConfig | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> ComplianceReport:
    cfg = config or load_config()
    report = ComplianceEngine(cfg.compliance.rules_dir).check(document)
    selected = provider or cfg.compliance.summary.provider
    if model is None:
        if selected == "openai":
            model = cfg.compliance.summary.openai_model
        elif selected == "gemini":
            model = cfg.compliance.summary.gemini_model
    return ComplianceSummarizer().summarize(
        report,
        provider=selected,
        model=model,
        max_output_tokens=cfg.compliance.summary.max_output_tokens,
    )

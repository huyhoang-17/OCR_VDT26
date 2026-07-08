"""Kiểu dữ liệu công khai của tầng tuân thủ."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class RiskLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class CheckStatus(str, Enum):
    PASS = "pass"
    VIOLATION = "violation"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class RuleDefinition:
    id: str
    form_type: str
    title: str
    severity: RiskLevel
    operation: str
    fields: dict[str, str]
    params: dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class RuleResult:
    rule_id: str
    title: str
    severity: RiskLevel
    status: CheckStatus
    message: str
    fields: dict[str, str] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)
    actual: Any = None
    expected: Any = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["status"] = self.status.value
        return data


@dataclass
class ComplianceReport:
    form_type: str
    checks: list[RuleResult]
    report_id: str = field(default_factory=lambda: f"CR-{uuid4().hex[:12].upper()}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: str = ""
    summary_source: str = "deterministic"
    warnings: list[str] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {status.value: sum(c.status == status for c in self.checks) for status in CheckStatus}

    @property
    def error_count(self) -> int:
        return sum(
            c.status == CheckStatus.VIOLATION and c.severity == RiskLevel.ERROR for c in self.checks
        )

    @property
    def warning_count(self) -> int:
        return sum(
            c.status == CheckStatus.VIOLATION and c.severity == RiskLevel.WARNING
            for c in self.checks
        )

    @property
    def overall_status(self) -> str:
        if not self.checks or all(c.status == CheckStatus.SKIPPED for c in self.checks):
            return "not_assessed"
        if self.error_count:
            return "non_compliant"
        if self.warning_count:
            return "compliant_with_warnings"
        return "compliant"

    def llm_payload(self) -> dict[str, Any]:
        """Chỉ dữ liệu ĐÃ TÍNH; không gửi JSON gốc để LLM tự suy luận/tính toán."""
        return {
            "form_type": self.form_type,
            "overall_status": self.overall_status,
            "counts": self.counts,
            "violations": [
                {
                    "rule_id": c.rule_id,
                    "title": c.title,
                    "severity": c.severity.value,
                    "message": c.message,
                    "actual": c.actual,
                    "expected": c.expected,
                }
                for c in self.checks
                if c.status == CheckStatus.VIOLATION
            ],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "form_type": self.form_type,
            "overall_status": self.overall_status,
            "counts": self.counts,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "summary": self.summary,
            "summary_source": self.summary_source,
            "warnings": self.warnings,
            "checks": [c.to_dict() for c in self.checks],
        }

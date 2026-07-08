"""Mô hình request/response cho REST API (để tài liệu /docs rõ ràng)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    default_engine: str


class FormsResponse(BaseModel):
    forms: dict[str, str]  # form_type -> mô tả


class EnginesResponse(BaseModel):
    engines: dict[str, bool]  # tên engine -> đã cài đủ dependency
    default: str


class ProcessResponse(BaseModel):
    form_type: Optional[str]
    output: dict[str, Any]          # JSON theo schema (gồm _meta)
    warnings: list[str]
    timings_ms: dict[str, float]
    ocr_engine: list[str]


class ComplianceRequest(BaseModel):
    document: dict[str, Any]
    provider: str = "deterministic"  # deterministic | openai | gemini
    model: Optional[str] = None


class ComplianceResponse(BaseModel):
    report: dict[str, Any]

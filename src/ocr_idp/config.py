"""Quản lý cấu hình: nạp từ file YAML + biến môi trường (.env), không hardcode.

Thứ tự ưu tiên (cao -> thấp):
    1. Tham số truyền trực tiếp khi gọi `load_config(overrides=...)`
    2. Biến môi trường `OCRIDP_*` (vd: OCRIDP_LOG_LEVEL, OCRIDP_OCR_ENGINE)
    3. Giá trị trong file YAML (mặc định: configs/default.yaml)
    4. Giá trị mặc định khai báo trong các model bên dưới

Bí mật (API key) KHÔNG nằm trong cấu hình này — đọc trực tiếp từ os.environ tại
nơi sử dụng (xem extract/llm_claude.py), để tránh vô tình log/serialize ra ngoài.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Các nhóm cấu hình con (1 nhóm ~ 1 bước pipeline)
# --------------------------------------------------------------------------- #
class PreprocessConfig(BaseModel):
    """[1] Tiền xử lý tài liệu."""

    target_dpi: int = 300
    max_side: int = 2500
    deskew: bool = True
    denoise: bool = True
    enhance_contrast: bool = True
    # none = giữ ảnh xám (tốt cho OCR học sâu: RapidOCR/VietOCR). otsu/adaptive/
    # sauvola hữu ích cho Tesseract hoặc ảnh nền bẩn.
    binarize: str = "none"  # none | otsu | adaptive | sauvola
    auto_crop: bool = True
    text_layer_min_chars: int = 50


class OCRConfig(BaseModel):
    """[2] OCR."""

    engine: str = "rapidocr"  # rapidocr | vietocr | paddle | easyocr | tesseract
    lang: str = "vi"
    use_gpu: bool = False
    min_text_confidence: float = 0.3
    # VietOCR: tên model dựng sẵn (vgg_transformer = chính xác hơn, vgg_seq2seq = nhẹ hơn)
    vietocr_model: str = "vgg_transformer"


class AnchorConfig(BaseModel):
    fuzzy_threshold: int = 80  # 0..100 (rapidfuzz)


class LLMConfig(BaseModel):
    """Cấu hình trích xuất bằng Claude. Mặc định TẮT; bật theo trường hoặc repair.

    LƯU Ý: KHÔNG gửi `temperature`/`top_p`/`budget_tokens` cho Opus 4.8/4.7 (API
    trả 400). Dùng structured output (output_config.format) thay vì các tham số đó.
    """

    enabled: bool = False
    model: str = "claude-opus-4-8"  # mặc định model mạnh nhất (xác nhận theo tài liệu claude-api)
    max_tokens: int = 2048
    # Khi enabled: dùng LLM bổ sung/sửa các trường thiếu hoặc độ tin cậy thấp
    repair: bool = True
    api_key_env: str = "ANTHROPIC_API_KEY"


class ExtractionConfig(BaseModel):
    """[4] Trích xuất trường."""

    default_strategy: str = "anchor"  # rule | anchor | layout | llm
    anchor: AnchorConfig = Field(default_factory=AnchorConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


class ValidationConfig(BaseModel):
    """[5] Chuẩn hóa & kiểm tra."""

    min_confidence: float = 0.6
    date_output_format: str = "%Y-%m-%d"


class ComplianceSummaryConfig(BaseModel):
    """LLM chỉ diễn đạt kết quả business-rule engine đã tính sẵn."""

    provider: str = "deterministic"  # deterministic | openai | gemini
    openai_model: str = "gpt-5.4-mini"
    gemini_model: str = "gemini-3-flash-preview"
    max_output_tokens: int = 700


class ComplianceConfig(BaseModel):
    """Tầng nghiệp vụ sau OCR/trích xuất."""

    enabled: bool = True
    rules_dir: str | None = None
    summary: ComplianceSummaryConfig = Field(default_factory=ComplianceSummaryConfig)


# --------------------------------------------------------------------------- #
# Cấu hình tổng
# --------------------------------------------------------------------------- #
class AppConfig(BaseModel):
    """Cấu hình toàn ứng dụng."""

    data_dir: str = "data"
    output_dir: str = "outputs"
    log_level: str = "INFO"

    preprocess: PreprocessConfig = Field(default_factory=PreprocessConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)

    # -- Tiện ích đường dẫn -------------------------------------------------- #
    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)


# --------------------------------------------------------------------------- #
# Nạp cấu hình
# --------------------------------------------------------------------------- #
# Bản đồ biến môi trường "phẳng" -> đường dẫn trong cấu hình (cho tiện dùng).
_ENV_OVERRIDES: dict[str, tuple[str, ...]] = {
    "OCRIDP_LOG_LEVEL": ("log_level",),
    "OCRIDP_DATA_DIR": ("data_dir",),
    "OCRIDP_OUTPUT_DIR": ("output_dir",),
    "OCRIDP_OCR_ENGINE": ("ocr", "engine"),
    "OCRIDP_COMPLIANCE_SUMMARY_PROVIDER": ("compliance", "summary", "provider"),
    "OCRIDP_COMPLIANCE_GEMINI_MODEL": ("compliance", "summary", "gemini_model"),
}


def _deep_set(d: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    """Gán `value` vào dict lồng nhau theo `path`, tạo nhánh nếu thiếu."""
    cur = d
    for key in path[:-1]:
        cur = cur.setdefault(key, {})
    cur[path[-1]] = value


def _default_config_path() -> str:
    return os.environ.get("OCRIDP_CONFIG", "configs/default.yaml")


def load_config(
    config_path: str | os.PathLike[str] | None = None,
    overrides: dict[str, Any] | None = None,
) -> AppConfig:
    """Nạp cấu hình theo thứ tự ưu tiên đã mô tả ở đầu module.

    Args:
        config_path: đường dẫn YAML; mặc định lấy từ OCRIDP_CONFIG hoặc
            configs/default.yaml. Nếu file không tồn tại -> dùng mặc định.
        overrides: dict ghi đè cuối cùng (ưu tiên cao nhất).
    """
    raw: dict[str, Any] = {}

    # (3) YAML
    path = Path(config_path) if config_path else Path(_default_config_path())
    if path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            raw = loaded

    # (2) Biến môi trường OCRIDP_*
    for env_key, dotted in _ENV_OVERRIDES.items():
        val = os.environ.get(env_key)
        if val is not None and val != "":
            _deep_set(raw, dotted, val)

    # (1) overrides truyền trực tiếp
    if overrides:
        for dotted, val in overrides.items():
            _deep_set(raw, tuple(dotted.split(".")), val)

    return AppConfig(**raw)

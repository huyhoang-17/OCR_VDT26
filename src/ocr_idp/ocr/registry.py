"""Registry engine OCR: đăng ký theo tên, tra cứu & khởi tạo theo cấu hình.

Engine tự đăng ký qua decorator `@register_engine`. Các module engine import
"lười" thư viện nặng (chỉ import khi khởi tạo/nhận diện) nên nạp registry rất nhẹ.
"""

from __future__ import annotations

from ..config import OCRConfig
from .base import OCREngine

_REGISTRY: dict[str, type[OCREngine]] = {}


def register_engine(cls: type[OCREngine]) -> type[OCREngine]:
    """Decorator: đăng ký 1 lớp engine vào registry theo `cls.name`."""
    _REGISTRY[cls.name] = cls
    return cls


def _ensure_loaded() -> None:
    """Import các module engine để decorator chạy (đăng ký vào registry)."""
    from . import rapidocr_engine  # noqa: F401  (RapidOCR — mặc định)
    from . import vietocr_engine  # noqa: F401  (VietOCR — chất lượng cao tiếng Việt)
    # Tesseract, EasyOCR, Paddle sẽ thêm ở M8.


def available_engines() -> dict[str, bool]:
    """Trả về {tên_engine: đã_cài_đủ_dependency}."""
    _ensure_loaded()
    return {name: cls.is_available() for name, cls in sorted(_REGISTRY.items())}


def get_engine(name: str, config: OCRConfig | None = None) -> OCREngine:
    """Khởi tạo engine theo tên. Lỗi rõ ràng nếu tên sai hoặc thiếu dependency."""
    _ensure_loaded()
    if name not in _REGISTRY:
        raise KeyError(
            f"Engine OCR không tồn tại: '{name}'. Hiện có: {sorted(_REGISTRY)}"
        )
    cls = _REGISTRY[name]
    if not cls.is_available():
        raise RuntimeError(
            f"Engine '{name}' thiếu dependency {cls.requires}. "
            f"Hãy cài thư viện tương ứng hoặc chạy bằng Docker."
        )
    return cls(config)

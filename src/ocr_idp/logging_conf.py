"""Thiết lập logging cho toàn ứng dụng.

Ưu tiên dùng `configs/logging.yaml` (dictConfig) nếu tồn tại; nếu không thì
dùng cấu hình mặc định: console đẹp (RichHandler nếu có) + file xoay vòng.
"""

from __future__ import annotations

import logging
import logging.config
import logging.handlers
from pathlib import Path

import yaml

_CONFIGURED = False


def setup_logging(
    level: str = "INFO",
    config_path: str | Path = "configs/logging.yaml",
    log_dir: str | Path = "logs",
) -> None:
    """Khởi tạo logging (idempotent — gọi nhiều lần chỉ tác dụng lần đầu)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    cfg_file = Path(config_path)
    if cfg_file.exists():
        try:
            cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
            logging.config.dictConfig(cfg)
            _CONFIGURED = True
            return
        except Exception as exc:  # noqa: BLE001 - fallback an toàn nếu YAML lỗi
            logging.getLogger(__name__).warning(
                "Không nạp được %s (%s); dùng logging mặc định.", cfg_file, exc
            )

    _setup_default(level, log_dir)
    _CONFIGURED = True


def _setup_default(level: str, log_dir: str | Path) -> None:
    """Cấu hình mặc định khi không có/không nạp được file YAML."""
    handlers: list[logging.Handler] = []

    # Console: dùng RichHandler nếu có, đẹp và dễ đọc
    try:
        from rich.console import Console
        from rich.logging import RichHandler

        # legacy_windows=False để không lỗi khi log Unicode lúc output bị capture
        console: logging.Handler = RichHandler(
            console=Console(legacy_windows=False, stderr=True),
            rich_tracebacks=True,
            show_path=False,
        )
        console.setFormatter(logging.Formatter("%(message)s", datefmt="%H:%M:%S"))
    except Exception:  # noqa: BLE001
        console = logging.StreamHandler()
        console.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%H:%M:%S")
        )
    handlers.append(console)

    # File log xoay vòng để debug
    file_handler = logging.handlers.RotatingFileHandler(
        Path(log_dir) / "ocr_idp.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%H:%M:%S")
    )
    handlers.append(file_handler)

    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=handlers)


def get_logger(name: str) -> logging.Logger:
    """Lấy logger theo tên module (đảm bảo đã setup tối thiểu)."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)

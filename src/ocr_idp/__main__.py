"""Cho phép chạy `python -m ocr_idp ...` tương đương lệnh `ocr-idp ...`."""

from .cli import app

if __name__ == "__main__":
    app()

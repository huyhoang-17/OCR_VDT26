"""REST API (FastAPI) cho OCR-IDP.

Endpoints:
  GET  /health   -> trạng thái + phiên bản + engine mặc định
  GET  /forms    -> danh sách biểu mẫu hỗ trợ
  GET  /engines  -> engine OCR + tình trạng cài đặt
  POST /process  -> upload PDF/ảnh (+ form_type, engine tùy chọn) -> JSON theo schema

Chạy:  uvicorn ocr_idp.api.app:app --host 0.0.0.0 --port 8000  (hoặc: ocr-idp serve-api)
Tài liệu tương tác: http://localhost:8000/docs
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse

from .. import __version__
from ..config import AppConfig, load_config
from ..logging_conf import get_logger
from .models import EnginesResponse, FormsResponse, HealthResponse, ProcessResponse

logger = get_logger(__name__)

app = FastAPI(
    title="OCR-IDP API",
    version=__version__,
    description="OCR & trích xuất dữ liệu (IDP) cho biểu mẫu chứng khoán tiếng Việt.",
)

# Cấu hình + pipeline khởi tạo LƯỜI và tái sử dụng (model OCR nạp 1 lần).
_state: dict[str, object] = {}


def _config() -> AppConfig:
    if "config" not in _state:
        _state["config"] = load_config(os.environ.get("OCRIDP_CONFIG"))
    return _state["config"]  # type: ignore[return-value]


def _pipeline():
    if "pipeline" not in _state:
        from ..pipeline import Pipeline

        _state["pipeline"] = Pipeline(_config())
    return _state["pipeline"]


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(version=__version__, default_engine=_config().ocr.engine)


@app.get("/forms", response_model=FormsResponse)
def forms() -> FormsResponse:
    from ..forms.base import list_forms

    return FormsResponse(forms=list_forms())


@app.get("/engines", response_model=EnginesResponse)
def engines() -> EnginesResponse:
    from ..ocr.registry import available_engines

    return EnginesResponse(engines=available_engines(), default=_config().ocr.engine)


@app.post("/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="File PDF/ảnh biểu mẫu."),
    form_type: Optional[str] = Form(None, description="Loại biểu mẫu (mặc định: tự đoán)."),
    engine: Optional[str] = Form(None, description="Engine OCR ghi đè."),
) -> ProcessResponse:
    """Chạy pipeline trên file upload -> JSON theo schema + cảnh báo."""
    suffix = Path(file.filename or "upload").suffix or ".bin"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File rỗng.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(content)
        tmp.close()

        # Engine ghi đè -> dùng pipeline riêng (không đụng pipeline mặc định đã cache)
        if engine:
            from ..pipeline import Pipeline

            cfg = load_config(os.environ.get("OCRIDP_CONFIG"))
            cfg.ocr.engine = engine
            pipe = Pipeline(cfg)
        else:
            pipe = _pipeline()

        result = pipe.run(tmp.name, form_type=form_type)
    except (KeyError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi xử lý file")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ: {exc}")
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    meta = result.output_json.get("_meta", {})
    return ProcessResponse(
        form_type=result.form_type,
        output=result.output_json,
        warnings=meta.get("warnings", []),
        timings_ms=result.timings_ms,
        ocr_engine=meta.get("ocr_engine", []),
    )

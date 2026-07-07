# =============================================================================
# Image chạy OCR-IDP với đầy đủ dependency hệ thống (Tesseract + poppler).
# Python 3.11 -> tương thích tốt với mọi engine (kể cả torch/paddle nếu thêm).
#
# Build (base + LLM + demo):
#   docker build -f docker/Dockerfile -t ocr-idp:latest .
# Build kèm engine nặng:
#   docker build -f docker/Dockerfile --build-arg EXTRAS=".[full,vietocr]" -t ocr-idp:full .
# =============================================================================
FROM python:3.11-slim

# --- Dependency hệ thống -----------------------------------------------------
# tesseract-ocr-vie: dữ liệu tiếng Việt cho Tesseract
# poppler-utils    : cho pdf2image (PyMuPDF không cần, nhưng để sẵn cho linh hoạt)
# libgl1/libglib   : cho OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Cài dependency trước (tận dụng layer cache) — chỉ copy metadata
COPY pyproject.toml requirements.txt ./
# Nhóm extras cài kèm; mặc định base + demo + llm + VietOCR (tiếng Việt chất lượng cao)
ARG EXTRAS=".[full,vietocr]"

# Copy mã nguồn rồi cài ở chế độ editable.
# Cài torch BẢN CPU trước (tránh kéo bản CUDA ~vài GB) để VietOCR/EasyOCR dùng lại.
COPY src ./src
COPY configs ./configs
RUN pip install --upgrade pip \
    && pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install -e "${EXTRAS}"

# Ghi chú: lần chạy VietOCR ĐẦU TIÊN sẽ tải trọng số model về (cần mạng).

# Thư mục dữ liệu/đầu ra (mount volume khi chạy)
RUN mkdir -p data/raw data/processed data/ground_truth outputs logs

EXPOSE 8000 8501

# Mặc định chạy REST API; docker-compose ghi đè command cho service web
CMD ["uvicorn", "ocr_idp.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

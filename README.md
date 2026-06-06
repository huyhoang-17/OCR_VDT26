# OCR-IDP — Hệ thống OCR & trích xuất dữ liệu cho biểu mẫu chứng khoán tiếng Việt

Pipeline **end-to-end**: nhận PDF/ảnh scan biểu mẫu chứng khoán tiếng Việt →
xuất **JSON có cấu trúc** đúng schema cho từng loại biểu mẫu (Intelligent
Document Processing).

> Trạng thái: đang phát triển theo mốc. **M0 — khung dự án** đã xong. Xem
> [Lộ trình](#lộ-trình-roadmap).

---

## Tính năng (mục tiêu)

- **Tiền xử lý**: render PDF→ảnh (PyMuPDF, không cần poppler), deskew, khử nhiễu,
  tăng tương phản, binarize, auto-crop; tự phát hiện PDF có text-layer để bỏ OCR.
- **OCR đa engine** sau một interface chung để so sánh: RapidOCR, VietOCR,
  Tesseract, EasyOCR, PaddleOCR.
- **Phân tích layout**: dòng/section, bảng, checkbox/radio, vùng dấu/chữ ký.
- **Trích xuất trường hybrid**: rule/regex + anchor/label (fuzzy) + layout +
  **LLM (Claude) structured output** — cấu hình theo từng trường, fallback rule.
- **Chuẩn hóa & kiểm tra**: ngày/tiền/mã định danh/tên/địa chỉ; gắn cờ trường
  thiếu / sai định dạng / confidence thấp.
- **Đánh giá**: accuracy/trường, exact-match, P/R, thời gian; bảng so sánh MD+CSV.
- **Demo**: REST API (FastAPI) + Web (Streamlit) + CLI (Typer).

## Kiến trúc

```
PDF/Ảnh → [1] Tiền xử lý → [2] OCR → [3] Layout → [4] Trích xuất → [5] Chuẩn hóa/Kiểm tra → JSON
```

Mỗi bước là một component có interface rõ ràng (xem `src/ocr_idp/types.py`).
Mỗi loại biểu mẫu là một **plugin** (`src/ocr_idp/forms/<form>/`) gồm schema +
cấu hình trích xuất + chuẩn hóa/validate riêng → thêm biểu mẫu mới **không sửa core**.

3 biểu mẫu mẫu (giả lập để chạy thử ngay):
| form_type | Mô tả | Thử thách trích xuất |
|---|---|---|
| `account_opening_individual` | Giấy mở tài khoản GDCK cá nhân | key-value theo nhãn + checkbox |
| `order_slip` | Phiếu lệnh giao dịch | radio + số (KL/giá) |
| `shareholder_list` | Danh sách người sở hữu CK | bảng nhiều dòng |

## Cấu trúc thư mục

```
.
├── configs/            # default.yaml (pipeline) + logging.yaml
├── data/               # raw / processed / ground_truth / synthetic / splits
├── docker/             # Dockerfile + docker-compose.yml
├── scripts/            # make_synthetic.py, run_end_to_end.py, run_eval.py
├── src/ocr_idp/        # mã nguồn (package)
│   ├── config.py types.py pipeline.py cli.py logging_conf.py
│   ├── preprocess/ ocr/ layout/ extract/ normalize/ validate/
│   ├── forms/          # plugin biểu mẫu
│   ├── eval/ api/ webapp/
└── tests/              # pytest
```

---

## Cài đặt

### Cách 1 (khuyến nghị): Docker

Docker đã đóng gói sẵn **Tesseract (+vie)** và **poppler**, dùng Python 3.11 nên
tương thích đầy đủ mọi engine (kể cả torch/paddle nếu thêm).

```powershell
# 1) Tạo file .env từ mẫu (điền ANTHROPIC_API_KEY nếu muốn bật LLM)
Copy-Item .env.example .env

# 2) Build + chạy API (:8000) và Web (:8501)
docker compose -f docker/docker-compose.yml up --build
```

- REST API docs: http://localhost:8000/docs
- Web demo: http://localhost:8501

### Cách 2: Windows-native (fallback)

> Khuyến nghị **Python 3.11 hoặc 3.12** (một số engine như VietOCR/EasyOCR cần
> torch và **chưa có wheel cho Python 3.14**). Bản cơ bản (RapidOCR + Tesseract)
> vẫn chạy được trên 3.10+.

```powershell
# Tạo & kích hoạt venv
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài bản cơ bản (RapidOCR + tiền xử lý + CLI)
pip install -e .

# (tùy chọn) cài thêm LLM + demo + dev
pip install -e ".[full]"

# (tùy chọn) engine nặng — cần build/torch
pip install -e ".[vietocr,easyocr]"
```

**Dependency hệ thống trên Windows:**

- **Tesseract OCR**: tải bản build UB-Mannheim
  (https://github.com/UB-Mannheim/tesseract/wiki), khi cài nhớ **chọn thêm gói
  ngôn ngữ Vietnamese (`vie`)**. Thêm thư mục cài vào `PATH`, hoặc đặt
  `TESSERACT_CMD` trong `.env`.
- **poppler** (chỉ cần nếu dùng pdf2image; PyMuPDF không cần): tải poppler cho
  Windows (https://github.com/oschwartz10612/poppler-windows/releases), giải nén
  và thêm thư mục `bin` vào `PATH`.

Kiểm tra môi trường:

```powershell
ocr-idp info
```

---

## Sử dụng

```powershell
ocr-idp version                 # phiên bản
ocr-idp info                    # kiểm tra môi trường + cấu hình
ocr-idp forms                   # liệt kê biểu mẫu hỗ trợ

# (từ M1) sinh dữ liệu giả lập
ocr-idp make-data

# (từ M4) chạy 1 file -> JSON
ocr-idp process data/synthetic/account_opening/sample_01.pdf `
    --form account_opening_individual -o out.json

# (từ M9) đánh giá so ground-truth
ocr-idp evaluate
```

Cũng có thể chạy bằng `python -m ocr_idp ...`.

## Cấu hình

- File chính: `configs/default.yaml` (DPI, engine OCR, ngưỡng, LLM...).
- Ghi đè bằng biến môi trường `OCRIDP_*` hoặc tham số `--config`.
- Bí mật (`ANTHROPIC_API_KEY`) đặt trong `.env` (không commit).

## Dữ liệu & ground-truth

```
data/raw/<form_type>/<ten_file>.pdf|png        # đầu vào gốc
data/ground_truth/<form_type>/<ten_file>.json  # nhãn vàng (đúng schema)
data/synthetic/<form_type>/...                 # dữ liệu giả lập (M1)
data/splits/{train,dev,test}.txt               # chia tập benchmark
```

## Kiểm thử

```powershell
pip install -e ".[dev]"
pytest
```

---

## Lộ trình (roadmap)

| Mốc | Nội dung | Trạng thái |
|---|---|---|
| M0 | Khung dự án, config, types, CLI, Docker, README | ✅ |
| M1 | 3 schema + sinh dữ liệu giả lập + ground-truth | ✅ |
| M2 | Tiền xử lý + test | ✅ |
| M3 | OCR (RapidOCR + interface + registry) + test | ✅ |
| M4 | Trích xuất tối thiểu + Form A + **MVP end-to-end** | ✅ |
| M5 | Layout (checkbox/radio, dấu/chữ ký, nền bảng) | ✅ |
| + | VietOCR (kéo lên sớm): RapidOCR(det)+VietOCR(rec) | ✅ |
| M6 | Trích xuất nâng cao (layout + Claude) | ⏳ |
| M7 | Chuẩn hóa/validate đầy đủ + Form B & C | ⏳ |
| M8 | Các engine OCR còn lại + benchmark | ⏳ |
| M9 | Bộ đánh giá (MD/CSV) | ⏳ |
| M10 | Demo: API + Web + CLI | ⏳ |
| M11 | Hoàn thiện: README, test, dọn dẹp | ⏳ |

## Giấy phép

MIT.

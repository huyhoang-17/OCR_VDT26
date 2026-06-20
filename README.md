# OCR-IDP — Hệ thống OCR & trích xuất dữ liệu cho biểu mẫu chứng khoán tiếng Việt

Pipeline **end-to-end**: nhận PDF/ảnh scan biểu mẫu chứng khoán tiếng Việt →
tiền xử lý → OCR (đa engine) → phân tích layout → trích xuất → **JSON**
(Intelligent Document Processing).

> **Trạng thái:** đang chạy trên **dữ liệu thật** — 9 biểu mẫu eform (PDF nhiều
> trang, phần lớn là ảnh scan). Pipeline xử lý **đa trang** an toàn và kết xuất
> OCR theo trang qua plugin `generic`. **Trích xuất riêng cho từng eform** (để
> output khớp `expect_N.json`) là phần phát triển tiếp theo — xem
> [Hiện trạng & hướng tiếp theo](#hiện-trạng--hướng-tiếp-theo).

---

## Tính năng

- **Tiền xử lý**: render PDF→ảnh (PyMuPDF, không cần poppler), deskew, khử nhiễu,
  tăng tương phản, binarize, auto-crop; tự phát hiện PDF có text-layer để bỏ OCR.
- **Đa trang**: mỗi tài liệu được xử lý đủ mọi trang; mỗi dòng OCR mang `page_index`
  nên trích xuất theo hình học không bị "rò rỉ" giữa các trang.
- **OCR đa engine** sau một interface chung: RapidOCR (mặc định), VietOCR,
  Tesseract, EasyOCR, PaddleOCR.
- **Phân tích layout**: dòng/section, bảng, checkbox/radio, vùng dấu/chữ ký.
- **Khung trích xuất hybrid** (sẵn sàng cho plugin chuyên biệt): rule/regex +
  anchor/label (fuzzy) + layout + **LLM (Claude) structured output** — cấu hình
  theo từng trường, tự fallback rule khi không có API key.
- **Chuẩn hóa & kiểm tra**: ngày/tiền/mã định danh/tên/địa chỉ; gắn cờ trường
  thiếu / sai định dạng / confidence thấp.
- **Đánh giá**: ghép input ↔ ground-truth, accuracy/trường, exact-match, P/R,
  thời gian → MD+CSV.
- **Demo**: REST API (FastAPI) + Web (Streamlit) + CLI (Typer).

## Kiến trúc

```
PDF/Ảnh → [1] Tiền xử lý → [2] OCR → [3] Layout → [4] Trích xuất → [5] Chuẩn hóa/Kiểm tra → JSON
```

Mỗi bước là một component có interface rõ ràng (xem `src/ocr_idp/types.py`).
Mỗi loại biểu mẫu là một **plugin** (`src/ocr_idp/forms/<form>/`) → thêm biểu mẫu
mới **không sửa core**. Hiện có 1 plugin:

| form_type | Mô tả |
|---|---|
| `generic` | Kết xuất OCR theo **từng trang** (`{form_type, page_count, pages:[{page_index, n_lines, lines, text}]}`). Dùng làm fallback khi chưa có plugin chuyên biệt cho biểu mẫu. |

## Dữ liệu thật

Dữ liệu là **9 biểu mẫu eform**, mỗi biểu mẫu một PDF nhiều trang, ghép với nhãn
vàng (JSON kỳ vọng) **theo số `N`**:

```
data/raw/form_<N>.pdf            # PDF gốc (đầu vào)
data/ground_truth/expect_<N>.json # nhãn vàng — schema bọc {run_id, status, form_id, results:{...}}
```

| form | trang | loại |
|---|--:|---|
| eform1 | 2 | PDF số (có text-layer) |
| eform5 | 3 | Scan (ảnh) |
| eform7 | 3 | Scan (ảnh) |
| eform69 | 3 | Scan (ảnh) |
| eform85 | 1 | Scan (ảnh) |
| eform92 | 2 | Scan (ảnh) |
| eform93 | 3 | Scan (ảnh) |
| eform94 | 6 | Scan (ảnh) |
| eform100 | 4 | Scan (ảnh) |

→ Bộ dữ liệu **hỗn hợp**: 1 PDF số (đọc qua text-layer, chính xác tuyệt đối) và
8 bản scan (bắt buộc OCR — chất lượng phụ thuộc engine; tiếng Việt nên dùng
VietOCR/Docker hoặc bật LLM repair để giữ dấu).

## Cấu trúc thư mục

```
.
├── configs/            # default.yaml (pipeline) + logging.yaml
├── data/               # raw/ (PDF gốc) + ground_truth/ (nhãn vàng) + processed/
├── docker/             # Dockerfile + docker-compose.yml
├── scripts/            # ocr_demo.py, preprocess_demo.py, run_eval.py
├── src/ocr_idp/        # mã nguồn (package)
│   ├── config.py types.py pipeline.py cli.py logging_conf.py
│   ├── preprocess/ ocr/ layout/ extract/ normalize/ validate/
│   ├── forms/          # plugin biểu mẫu (forms/generic/)
│   ├── eval/ api/ webapp/
└── tests/              # pytest (89 test)
```

---

## Cài đặt

### Cách 1 (khuyến nghị): Docker

Docker đóng gói sẵn **Tesseract (+vie)** và **poppler**, dùng Python 3.11 nên
tương thích đầy đủ mọi engine (kể cả torch/paddle).

```powershell
# 1) Tạo .env từ mẫu (điền ANTHROPIC_API_KEY nếu muốn bật LLM)
Copy-Item .env.example .env

# 2) Build + chạy API (:8000) và Web (:8501)
docker compose -f docker/docker-compose.yml up --build
```

- REST API docs: http://localhost:8000/docs
- Web demo: http://localhost:8501

### Cách 2: Windows-native (fallback)

> Khuyến nghị **Python 3.11/3.12** (VietOCR/EasyOCR cần torch, **chưa có wheel cho
> Python 3.14**). Bản cơ bản (RapidOCR + Tesseract) chạy được trên 3.10+.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e .                 # bản cơ bản (RapidOCR + tiền xử lý + CLI)
pip install -e ".[full]"         # (tùy chọn) LLM + demo + dev
pip install -e ".[vietocr,easyocr]"  # (tùy chọn) engine nặng
```

**Dependency hệ thống (Windows):**

- **Tesseract OCR**: bản UB-Mannheim (https://github.com/UB-Mannheim/tesseract/wiki),
  nhớ **chọn gói ngôn ngữ Vietnamese (`vie`)**; thêm vào `PATH` hoặc đặt
  `TESSERACT_CMD` trong `.env`.
- **poppler** (chỉ cần nếu dùng pdf2image; PyMuPDF không cần).

```powershell
ocr-idp info     # kiểm tra môi trường + cấu hình
```

---

## Sử dụng

```powershell
ocr-idp version                 # phiên bản
ocr-idp info                    # kiểm tra môi trường + cấu hình
ocr-idp forms                   # liệt kê biểu mẫu hỗ trợ (hiện: generic)

# Chạy 1 file -> JSON (tự đoán biểu mẫu; chưa có plugin riêng -> fallback generic)
ocr-idp process data/raw/form_1.pdf -o out.json

# Xử lý cả thư mục -> 1 JSON / file
ocr-idp batch data/raw -o outputs/json

# Đánh giá so ground-truth (ghép form_N.pdf ↔ expect_N.json theo N) -> outputs/eval_*.{md,csv}
ocr-idp evaluate --kind pdf      # dùng text-layer nếu có
ocr-idp evaluate --kind scan     # ép OCR mọi trang (đo chất lượng OCR)
ocr-idp evaluate --form eform7   # chỉ 1 biểu mẫu

# Demo cục bộ (không cần Docker)
ocr-idp serve-api                # REST API: http://127.0.0.1:8000/docs
ocr-idp serve-web                # Web demo: http://localhost:8501
```

Cũng có thể chạy bằng `python -m ocr_idp ...`.

## Cấu hình

- File chính: `configs/default.yaml` (DPI, engine OCR, ngưỡng, LLM...).
- Ghi đè bằng biến môi trường `OCRIDP_*` hoặc tham số `--config`.
- Bí mật (`ANTHROPIC_API_KEY`) đặt trong `.env` (không commit).

## REST API

```powershell
pip install -e ".[api]"
ocr-idp serve-api               # http://127.0.0.1:8000/docs
```

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/health` | trạng thái + phiên bản + engine mặc định |
| GET | `/forms` | danh sách biểu mẫu hỗ trợ |
| GET | `/engines` | engine OCR + tình trạng cài đặt |
| POST | `/process` | upload PDF/ảnh (+ `form_type`, `engine` tùy chọn) → JSON |

```bash
curl -X POST http://localhost:8000/process \
  -F "file=@data/raw/form_1.pdf"
# -> { "form_type": "generic",
#      "output": { "page_count": 2, "pages": [ {"page_index":0,"lines":[...],"text":"..."}, ... ] },
#      "warnings": [], "timings_ms": {...}, "ocr_engine": ["textlayer"] }
```

## Hiện trạng & hướng tiếp theo

**Đã có:** pipeline đa trang chạy trên cả 9 biểu mẫu thật; plugin `generic` kết
xuất OCR theo trang; harness đánh giá ghép `raw/form_N.pdf ↔ ground_truth/expect_N.json`.

**Chưa có:** trích xuất riêng cho từng eform để output khớp `expect_N.json` (mỗi
eform là một schema khác nhau với khóa dạng `EformzzContentItems...`). Vì vậy
`ocr-idp evaluate` hiện cho **baseline** (generic ≠ schema eform) — dùng để đo
mức xuất phát, chưa phải độ chính xác trích xuất.

**Thêm plugin chuyên biệt cho 1 eform** = tạo `src/ocr_idp/forms/<form_type>/`:

1. `schema.json` — JSON Schema output mong muốn.
2. `extraction.yaml` — khai báo từng trường: `name` (dot-path), `strategy`
   (`anchor` | `rule` | `layout` | `checkbox` | `radio` | `table` | `signature` |
   `llm`), `anchor`/`regex`/`options`, `normalizer`, `required`.
3. `plugin.py` — lớp con `FormPlugin` gắn `@register_form`, khai báo `form_type`,
   `title`, `classify_keywords` (để tự nhận diện).

Rồi import nó trong `forms/base.py::_ensure_loaded()` — pipeline tự dùng qua
registry (`ocr-idp forms` sẽ liệt kê). `normalizer` có sẵn: `string`, `date`,
`datetime`, `int`, `money`, `price`, `percent`, `phone`, `email`, `id_number`,
`account_number`, `symbol`.

## Kiểm thử

```powershell
pip install -e ".[dev]"
pytest                # 89 test (có test chạy OCR thật trên data/raw)
```

---

## Lộ trình (roadmap)

Khung pipeline (M0–M11) đã hoàn thiện trên **dữ liệu giả lập**; sau đó dự án
**chuyển sang dữ liệu thật** (9 eform) và điều chỉnh tương ứng:

| Mốc | Nội dung | Trạng thái |
|---|---|---|
| M0–M3 | Khung dự án, config/types/CLI/Docker; tiền xử lý; OCR + registry | ✅ |
| M4–M7 | Khung trích xuất (anchor/rule/layout/checkbox/radio/table) + LLM + chuẩn hóa/validate | ✅ |
| M8–M9 | Đa engine OCR; bộ đánh giá so ground-truth (accuracy/exact/P-R-F1/lỗi → MD/CSV) | ✅ |
| M10–M11 | Demo REST API + Web + CLI; hoàn thiện | ✅ |
| **Chuyển dữ liệu thật** | Đa trang an toàn (`page_index`); gỡ toàn bộ dữ liệu/code synthetic; plugin `generic`; eval ghép `raw ↔ ground_truth` theo N | ✅ |
| **Tiếp theo** | Plugin trích xuất riêng cho từng eform (khớp `expect_N.json`); hoặc tầng kiểm tra nghiệp vụ trên JSON kỳ vọng | ⏳ |

## Giấy phép

MIT.

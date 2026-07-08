# OCR-IDP — Hệ thống OCR & trích xuất dữ liệu cho biểu mẫu chứng khoán tiếng Việt

Pipeline **end-to-end**: nhận PDF/ảnh scan biểu mẫu chứng khoán tiếng Việt →
tiền xử lý → OCR (đa engine) → phân tích layout → trích xuất → **JSON** → kiểm tra
nghiệp vụ liên-trường → **biên bản tuân thủ DOCX/PDF**.

> **Trạng thái:** đang chạy trên **dữ liệu thật** — 9 biểu mẫu eform (PDF nhiều
> trang, phần lớn là ảnh scan). Pipeline xử lý **đa trang** an toàn và kết xuất
> OCR theo trang qua plugin `generic`. **Extractor riêng cho cả 9 eform** đã có
> và xuất JSON theo schema của `expect_N.json` — xem kết quả tại
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
- **Business-rule engine**: luật YAML theo từng eform; đối soát tổng, phép nhân
  tiền/số lượng, giới hạn vốn và thứ tự ngày. Phép tính hoàn toàn tất định.
- **Biên bản tuân thủ**: bảng đạt/vi phạm/chưa đánh giá, mức lỗi/cảnh báo, xuất
  Markdown/DOCX/PDF; OpenAI hoặc Gemini chỉ diễn đạt bản tóm tắt và tự fallback.
- **Benchmark nghiệp vụ**: chèn lỗi số học/thời gian nhân tạo, đo P/R/F1 độc lập OCR.
- **Demo**: REST API (FastAPI) + Web (Streamlit) + CLI (Typer).

## Kiến trúc

```
PDF/Ảnh → [1..5] OCR/IDP → JSON → [6] Business rules → [7] Biên bản + tóm tắt LLM
```

Mỗi bước là một component có interface rõ ràng (xem `src/ocr_idp/types.py`).
Mỗi loại biểu mẫu là một **plugin** (`src/ocr_idp/forms/<form>/`) → thêm biểu mẫu
mới **không sửa core**. Hiện có 10 plugin:

| form_type | Mô tả |
|---|---|
| `eform1/5/7/69/85/92/93/94/100` | **Extractor chuyên biệt** cho 9 eform thật → JSON khớp `expect_N.json`. Đa số dùng base `RegexFormPlugin` (bảng RULES); eform1 dùng `extract()` tùy biến (text-layer). |
| `generic` | Kết xuất OCR theo **từng trang** (`{form_type, page_count, pages:[{page_index, n_lines, lines, text}]}`). Dùng làm fallback khi không nhận diện được biểu mẫu. |

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
│   ├── compliance/     # engine, luật YAML/eform, benchmark, LLM summary, DOCX/PDF
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
# 1) Tạo .env từ mẫu (API key chỉ cần khi bật LLM)
Copy-Item .env.example .env

# 2) Build + chạy API (:8000) và Web (:8501)
docker compose -f docker/docker-compose.yml up --build
```

```powershell
# Hủy chạy docker
docker compose -f docker/docker-compose.yml down
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
ocr-idp forms                   # liệt kê biểu mẫu hỗ trợ (9 eform + generic)

# Chạy 1 file -> JSON (tự đoán biểu mẫu; chưa có plugin riêng -> fallback generic)
ocr-idp process data/raw/form_1.pdf -o out.json

# Xử lý cả thư mục -> 1 JSON / file
ocr-idp batch data/raw -o outputs/json

# Đánh giá so ground-truth (ghép form_N.pdf ↔ expect_N.json theo N) -> outputs/eval_*.{md,csv}
ocr-idp evaluate --kind pdf      # dùng text-layer nếu có
ocr-idp evaluate --kind scan     # ép OCR mọi trang (đo chất lượng OCR)
ocr-idp evaluate --form eform7   # chỉ 1 biểu mẫu
ocr-idp evaluate --kind scan --engine rapidocr
ocr-idp evaluate --kind scan --engine tesseract
ocr-idp evaluate --kind scan --engine vietocr

# Tầng nghiệp vụ chạy trực tiếp trên JSON, không gọi lại OCR
ocr-idp check-compliance data/ground_truth/expect_1.json `
  --output outputs/compliance.json `
  --docx outputs/compliance.docx `
  --pdf outputs/compliance.pdf

# Chèn lỗi nghiệp vụ nhân tạo và đo P/R/F1 riêng
ocr-idp evaluate-compliance --data data/ground_truth --out outputs

# Demo cục bộ (không cần Docker)
ocr-idp serve-api                # REST API: http://127.0.0.1:8000/docs
ocr-idp serve-web                # Web demo: http://localhost:8501
```

Cũng có thể chạy bằng `python -m ocr_idp ...`.

## Cấu hình

- File chính: `configs/default.yaml` (DPI, engine OCR, ngưỡng, LLM...).
- Ghi đè bằng biến môi trường `OCRIDP_*` hoặc tham số `--config`.
- Tóm tắt mặc định `deterministic` (offline). Đổi bằng
  `OCRIDP_COMPLIANCE_SUMMARY_PROVIDER=openai|gemini`.
- Bí mật (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) đặt trong
  `.env` (không commit).

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
| POST | `/compliance/check` | nhận JSON đã trích xuất → kết quả kiểm tra + tóm tắt |
| POST | `/compliance/report?format=docx\|pdf` | nhận JSON → tải biên bản tuân thủ |

```bash
curl -X POST http://localhost:8000/process \
  -F "file=@data/raw/form_1.pdf"
# -> { "form_type": "generic",
#      "output": { "page_count": 2, "pages": [ {"page_index":0,"lines":[...],"text":"..."}, ... ] },
#      "warnings": [], "timings_ms": {...}, "ocr_engine": ["textlayer"] }
```

## Hiện trạng & hướng tiếp theo

**Đã có:** pipeline đa trang chạy trên cả 9 biểu mẫu thật; plugin `generic`
(fallback kết xuất OCR theo trang); **extractor chuyên biệt cho CẢ 9 eform**
(eform1/5/7/69/85/92/93/94/100); harness đánh giá ghép `raw/form_N.pdf ↔
ground_truth/expect_N.json`.

### Đánh giá 3 OCR engine trên extractor

Benchmark dùng cùng **9 extractor**, 9 PDF (27 trang), 472 trường ground-truth và
`--kind scan` để buộc mọi trang đi qua OCR. Vì vậy bảng dưới đo ảnh hưởng của engine
OCR lên kết quả trích xuất bằng các extractor chuyên biệt, không dùng text-layer.

| Engine | Accuracy/trường | Precision | Recall | F1 | Lỗi missing / OCR / format |
|---|--:|--:|--:|--:|---:|
| **VietOCR** | **47.5%** (224/472) | 93.5% | **39.1%** | 55.1% | **233** / 10 / 5 |
| **RapidOCR** | 47.2% (223/472) | **97.5%** | 38.8% | **55.5%** | 241 / **4** / **4** |
| **Tesseract** | 47.0% (222/472) | 95.2% | 38.6% | 54.9% | 238 / 8 / **4** |

Accuracy theo từng extractor:

| eform | RapidOCR | Tesseract | VietOCR | Tốt nhất |
|---|--:|--:|--:|---|
| eform1 | 19.1% | 48.9% | **61.7%** | VietOCR |
| eform100 | **64.0%** | 60.0% | 58.0% | RapidOCR |
| eform5 | **58.6%** | 55.2% | 50.0% | RapidOCR |
| eform69 | **59.4%** | 57.8% | 56.2% | RapidOCR |
| eform7 | **38.9%** | 27.8% | 31.9% | RapidOCR |
| eform85 | 57.1% | **71.4%** | 61.9% | Tesseract |
| eform92 | **62.1%** | 48.3% | 44.8% | RapidOCR |
| eform93 | **18.2%** | 16.4% | 16.4% | RapidOCR |
| eform94 | 55.3% | 55.3% | **56.6%** | VietOCR |

**Kết luận:** ba engine gần như ngang nhau về accuracy tổng (chênh tối đa 0.5 điểm
phần trăm). VietOCR đứng đầu accuracy và cải thiện mạnh eform1 nhờ giữ dấu; RapidOCR
đạt precision/F1 cao nhất và tốt nhất trên 6/9 extractor; Tesseract nổi bật ở
eform85. Nút thắt hiện tại không chỉ là dấu tiếng Việt mà còn là độ bao phủ của
regex và trường **bảng** (đặc biệt BagPart của eform69/93), nên đổi engine đơn thuần
chưa tạo ra bước nhảy lớn.

Luồng `--kind pdf` dùng text-layer khi có vẫn đạt **54.4%** accuracy và **98.0%**
precision; đây là chế độ chạy thực tế, không dùng để xếp hạng ba OCR engine.

### Tầng nghiệp vụ sau OCR

Tầng này chỉ đọc object `results` từ JSON, **không chạy hoặc sửa OCR**. Hiện có
**41 luật YAML** cho đủ 9 eform với năm toán tử được phép: `equals_product`,
`less_or_equal`, `sum_equals`, `date_order`, `years_between`. Không dùng `eval`;
trường thiếu/sai kiểu được đánh dấu `skipped`, không bị quy thành vi phạm nghiệp vụ.

Kết quả trên 9 JSON ground-truth: 37 luật đạt và engine chủ động phát hiện 4 bất
nhất có sẵn:

- eform93: tỷ lệ cá nhân trong nước `20%` + nước ngoài `0%` khác tổng `80%`.
- eform94: vốn huy động thêm `300.000.000.000.000` khác
  `30.000.000 × 10.000 = 300.000.000.000`; vốn sau thay đổi `500 tỷ` khác
  `80.000.000 × 10.000 = 800 tỷ`; tổng vốn sau sáp nhập không khớp các cấu phần.

Benchmark chèn lỗi chỉ đo các luật đang đạt ở dữ liệu gốc, đồng thời loại các vi
phạm có sẵn khỏi nhãn dự đoán:

| Ca chèn lỗi | TP | FP | FN | Precision | Recall | F1 |
|--:|--:|--:|--:|--:|--:|--:|
| **35** | 35 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** |

LLM không nhận toàn bộ JSON nguồn mà chỉ nhận payload gồm kết luận, bộ đếm và danh
sách vi phạm **đã tính xong** (`actual`/`expected`). Nếu package, API key hoặc lời
gọi mạng lỗi, biên bản vẫn sinh bình thường bằng tóm tắt deterministic.

**Cấu trúc một extractor eform** = `src/ocr_idp/forms/<form>/plugin.py`: lớp con
`RegexFormPlugin` (`forms/_regex_plugin.py`) chỉ khai báo `form_type`, `title`,
`classify_keywords` và bảng `RULES` — mỗi dòng `(khóa_kết_quả, kind, regex[, options])`
với `kind` ∈ `text | date | date_dmy | digits | dong | phone | choice`. Rồi import
trong `forms/base.py::_ensure_loaded()`; `eval/report.py` tự dùng extractor theo
tên file. (eform1 dùng `extract()` tùy biến vì là text-layer tiếng Việt có dấu —
xem `forms/eform1/plugin.py`.)

## Kiểm thử

```powershell
pip install -e ".[dev]"
pytest                # 103 test (OCR + rule engine + API + DOCX/PDF)
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
| **Extractor 9 eform** | Plugin chuyên biệt cho cả 9 eform (`RegexFormPlugin`) → **54.4%** ở luồng pdf | ✅ |
| **So sánh OCR** | RapidOCR 47.2%, Tesseract 47.0%, VietOCR 47.5% trên cùng 9 extractor (`--kind scan`) | ✅ |
| **Tầng nghiệp vụ** | 41 luật/9 eform; benchmark 35 lỗi nhân tạo đạt P/R/F1 100%; OpenAI/Gemini summary; DOCX/PDF; CLI/API/Web | ✅ |
| **Tiếp theo** | Tăng độ bao phủ extractor; table-extraction cho bảng BagPart (eform69/93); mở rộng catalogue luật khi có đặc tả nghiệp vụ chính thức | ⏳ |

## Giấy phép

MIT.

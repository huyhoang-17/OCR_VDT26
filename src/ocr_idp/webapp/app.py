"""Web demo (Streamlit) cho OCR-IDP — chạy pipeline ngay trong tiến trình.

Luồng: upload PDF/ảnh -> chọn biểu mẫu/engine -> xem ảnh tiền xử lý + overlay
bbox OCR + JSON kết quả + bảng cảnh báo (trường cần kiểm tra) -> tải JSON.

Chạy:  streamlit run src/ocr_idp/webapp/app.py   (hoặc: ocr-idp serve-web)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from ocr_idp import __version__
from ocr_idp.config import load_config
from ocr_idp.forms.base import list_forms
from ocr_idp.ocr.overlay import draw_ocr_overlay
from ocr_idp.ocr.registry import available_engines
from ocr_idp.pipeline import Pipeline

st.set_page_config(page_title="OCR-IDP Demo", layout="wide")

_AUTO = "(tự đoán)"


def _run(file_bytes: bytes, suffix: str, form_type, engine: str, use_text_layer: bool):
    cfg = load_config()
    cfg.ocr.engine = engine
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(file_bytes)
        tmp.close()
        return Pipeline(cfg).run(tmp.name, form_type=form_type, use_text_layer=use_text_layer)
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass


def main() -> None:
    st.title("OCR-IDP — Trích xuất dữ liệu biểu mẫu chứng khoán")
    st.caption(f"Phiên bản {__version__} · PDF/ảnh → JSON có cấu trúc")

    with st.sidebar:
        st.header("Tùy chọn")
        forms = list_forms()
        form_choice = st.selectbox("Loại biểu mẫu", [_AUTO, *forms.keys()],
                                   format_func=lambda k: k if k == _AUTO else f"{k} — {forms[k]}")
        engines = [n for n, ok in available_engines().items() if ok] or ["rapidocr"]
        default_idx = engines.index("rapidocr") if "rapidocr" in engines else 0
        engine = st.selectbox("Engine OCR", engines, index=default_idx)
        use_text_layer = st.checkbox("Dùng text-layer PDF (nhanh & chính xác)", value=True)
        show_overlay = st.checkbox("Hiện overlay bbox OCR", value=True)

    uploaded = st.file_uploader("Tải lên PDF hoặc ảnh biểu mẫu", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded is None:
        st.info("Hãy tải lên một file để bắt đầu.")
        return

    if not st.button("Chạy trích xuất", type="primary"):
        return

    form_type = None if form_choice == _AUTO else form_choice
    suffix = Path(uploaded.name).suffix or ".bin"
    with st.spinner("Đang xử lý..."):
        try:
            result = _run(uploaded.getvalue(), suffix, form_type, engine, use_text_layer)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Lỗi: {exc}")
            return

    meta = result.output_json.get("_meta", {})
    warnings = meta.get("warnings", [])
    c1, c2, c3 = st.columns(3)
    c1.metric("Biểu mẫu", result.form_type or "—")
    c2.metric("Engine OCR", ", ".join(meta.get("ocr_engine", [])) or "—")
    c3.metric("Số cảnh báo", len(warnings))

    left, right = st.columns(2)
    with left:
        st.subheader("Ảnh & overlay OCR")
        if result.pages:
            page = result.pages[0]
            if show_overlay and result.ocr_results:
                st.image(draw_ocr_overlay(page.image, result.ocr_results[0]),
                         channels="BGR", caption="Overlay bbox OCR (trang 1)")
            else:
                st.image(page.image, caption="Ảnh đã tiền xử lý (trang 1)")
        st.caption(f"Thời gian (ms): {result.timings_ms}")
    with right:
        st.subheader("JSON kết quả")
        st.json(result.output_json)
        st.download_button(
            "Tải JSON", json.dumps(result.output_json, ensure_ascii=False, indent=2),
            file_name=f"{Path(uploaded.name).stem}.json", mime="application/json",
        )

    st.subheader("Cảnh báo cần kiểm tra")
    if warnings:
        st.table({"#": list(range(1, len(warnings) + 1)), "Nội dung": warnings})
    else:
        st.success("Không có cảnh báo — mọi trường đạt ngưỡng tin cậy.")


main()

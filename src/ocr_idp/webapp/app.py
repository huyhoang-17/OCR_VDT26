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

    if st.button("Chạy trích xuất", type="primary"):
        form_type = None if form_choice == _AUTO else form_choice
        suffix = Path(uploaded.name).suffix or ".bin"
        with st.spinner("Đang xử lý..."):
            try:
                result = _run(uploaded.getvalue(), suffix, form_type, engine, use_text_layer)
            except Exception as exc:  # noqa: BLE001
                st.session_state.pop("result", None)
                st.error(f"Lỗi: {exc}")
                return
        # Lưu kết quả để các lần rerun sau (vd kéo thanh chọn trang) vẫn hiển thị.
        st.session_state["result"] = result
        st.session_state["result_name"] = uploaded.name

    result = st.session_state.get("result")
    if result is None:
        st.info("Bấm **Chạy trích xuất** để xử lý file.")
        return
    src_name = st.session_state.get("result_name", uploaded.name)

    meta = result.output_json.get("_meta", {})
    warnings = meta.get("warnings", [])
    c1, c2, c3 = st.columns(3)
    c1.metric("Biểu mẫu", result.form_type or "—")
    c2.metric("Engine OCR", ", ".join(meta.get("ocr_engine", [])) or "—")
    c3.metric("Số cảnh báo", len(warnings))

    left, right = st.columns(2)
    with left:
        st.subheader("Ảnh & overlay OCR")
        n_pages = len(result.pages)
        if n_pages:
            # Tài liệu nhiều trang -> cho chọn trang để xem (mặc định trang 1).
            pidx = (st.slider("Trang", 1, n_pages, 1) - 1) if n_pages > 1 else 0
            page = result.pages[pidx]
            ocr = result.ocr_results[pidx] if pidx < len(result.ocr_results) else None
            cap_suffix = f"trang {pidx + 1}/{n_pages}"
            if show_overlay and ocr is not None:
                st.image(draw_ocr_overlay(page.image, ocr),
                         channels="BGR", caption=f"Overlay bbox OCR ({cap_suffix})")
            else:
                st.image(page.image, caption=f"Ảnh đã tiền xử lý ({cap_suffix})")
            if ocr is not None:
                with st.expander(f"Text OCR {cap_suffix} ({len(ocr.lines)} dòng)"):
                    st.text("\n".join(ln.text for ln in ocr.lines) or "(không có dòng nào)")
        st.caption(f"Thời gian (ms): {result.timings_ms}")
    with right:
        st.subheader("JSON kết quả")
        st.json(result.output_json)
        st.download_button(
            "Tải JSON", json.dumps(result.output_json, ensure_ascii=False, indent=2),
            file_name=f"{Path(src_name).stem}.json", mime="application/json",
        )

    st.subheader("Cảnh báo cần kiểm tra")
    if warnings:
        st.table({"#": list(range(1, len(warnings) + 1)), "Nội dung": warnings})
    else:
        st.success("Không có cảnh báo — mọi trường đạt ngưỡng tin cậy.")


main()

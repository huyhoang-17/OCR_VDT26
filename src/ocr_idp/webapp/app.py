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
        summary_provider = st.selectbox(
            "Tóm tắt biên bản", ["deterministic", "openai", "gemini"], index=0,
            help="OpenAI/Gemini chỉ diễn đạt kết quả luật đã tính; thiếu key sẽ tự fallback.",
        )

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

    st.subheader("Kiểm tra nghiệp vụ liên-trường")
    # Cache theo chính JSON đầu vào: đổi trang/overlay không làm chạy lại rule hoặc LLM.
    fingerprint = json.dumps(result.output_json, ensure_ascii=False, sort_keys=True, default=str)
    if st.session_state.get("compliance_fingerprint") != fingerprint:
        try:
            from ocr_idp.compliance.service import build_compliance_report

            st.session_state["compliance_report"] = build_compliance_report(
                result.output_json, provider="deterministic"
            )
            st.session_state["compliance_fingerprint"] = fingerprint
        except ValueError:
            st.session_state.pop("compliance_report", None)

    compliance = st.session_state.get("compliance_report")
    if compliance is None:
        st.info("Biểu mẫu này chưa có dữ liệu `results` hoặc chưa có bộ luật nghiệp vụ.")
        return

    if summary_provider != "deterministic" and st.button(
        f"Sinh tóm tắt bằng {summary_provider.title()}"
    ):
        from ocr_idp.compliance.service import build_compliance_report

        with st.spinner(f"Đang gọi {summary_provider}..."):
            compliance = build_compliance_report(
                result.output_json, provider=summary_provider
            )
        st.session_state["compliance_report"] = compliance

    counts = compliance.counts
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Kết luận", compliance.overall_status)
    b2.metric("Đạt", counts["pass"])
    b3.metric("Vi phạm", counts["violation"])
    b4.metric("Chưa đánh giá", counts["skipped"])
    st.caption(f"Tóm tắt ({compliance.summary_source})")
    st.write(compliance.summary)
    rows = [
        {
            "Mã luật": c.rule_id,
            "Mức độ khi vi phạm": c.severity.value,
            "Kết quả": c.status.value,
            "Nội dung": c.message,
            "Thực tế": c.actual,
            "Kỳ vọng": c.expected,
        }
        for c in compliance.checks
    ]
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info(f"Chưa khai báo luật nghiệp vụ cho {compliance.form_type}.")

    from ocr_idp.compliance.report import to_docx, to_pdf

    d1, d2 = st.columns(2)
    d1.download_button(
        "Tải biên bản DOCX", to_docx(compliance),
        file_name=f"compliance-{compliance.form_type}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    try:
        pdf_bytes = to_pdf(compliance)
        d2.download_button(
            "Tải biên bản PDF", pdf_bytes,
            file_name=f"compliance-{compliance.form_type}.pdf", mime="application/pdf",
        )
    except RuntimeError as exc:
        d2.warning(str(exc))


main()

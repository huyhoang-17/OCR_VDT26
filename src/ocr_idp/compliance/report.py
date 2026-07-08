"""Xuất biên bản tuân thủ Markdown, DOCX và PDF."""

from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from .models import ComplianceReport

_STATUS_VI = {"pass": "ĐẠT", "violation": "VI PHẠM", "skipped": "CHƯA ĐÁNH GIÁ"}
_RISK_VI = {"error": "Lỗi", "warning": "Cảnh báo"}


def to_markdown(report: ComplianceReport) -> str:
    lines = [
        "# BIÊN BẢN KIỂM TRA TUÂN THỦ",
        "",
        f"- Mã biên bản: `{report.report_id}`",
        f"- Biểu mẫu: `{report.form_type}`",
        f"- Thời điểm (UTC): {report.created_at}",
        f"- Kết luận: **{report.overall_status}**",
        "",
        "## Tóm tắt",
        "",
        report.summary,
        "",
        "## Kết quả chi tiết",
        "",
        "| # | Mã luật | Mức độ khi vi phạm | Kết quả | Nội dung | Thực tế | Kỳ vọng |",
        "|--:|---|---|---|---|---|---|",
    ]
    for i, check in enumerate(report.checks, 1):
        cells = [
            str(i), check.rule_id, _RISK_VI[check.severity.value],
            _STATUS_VI[check.status.value], check.message,
            "" if check.actual is None else str(check.actual),
            "" if check.expected is None else str(check.expected),
        ]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    if report.warnings:
        lines += ["", "## Ghi chú hệ thống", "", *[f"- {w}" for w in report.warnings]]
    lines += [
        "", "---", "",
        "Các phép tính và kết luận đạt/vi phạm do business-rule engine thực hiện. "
        "LLM (nếu bật) chỉ diễn đạt phần tóm tắt.",
    ]
    return "\n".join(lines) + "\n"


def to_docx(report: ComplianceReport) -> bytes:
    """Tạo DOCX tối giản bằng OpenXML chuẩn, không cần Microsoft Word/python-docx."""
    rows = [
        ["#", "Mã luật", "Mức độ khi vi phạm", "Kết quả", "Nội dung", "Thực tế", "Kỳ vọng"]
    ]
    for i, c in enumerate(report.checks, 1):
        rows.append([
            str(i), c.rule_id, _RISK_VI[c.severity.value], _STATUS_VI[c.status.value],
            c.message, "" if c.actual is None else str(c.actual),
            "" if c.expected is None else str(c.expected),
        ])

    def paragraph(text: str, bold: bool = False) -> str:
        props = "<w:rPr><w:b/></w:rPr>" if bold else ""
        return f'<w:p><w:r>{props}<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

    def cell(text: str) -> str:
        return f"<w:tc><w:tcPr/><w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p></w:tc>"

    table = "<w:tbl><w:tblPr><w:tblBorders>" + "".join(
        f'<w:{edge} w:val="single" w:sz="4" w:color="808080"/>'
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV")
    ) + "</w:tblBorders></w:tblPr>" + "".join(
        "<w:tr>" + "".join(cell(value) for value in row) + "</w:tr>" for row in rows
    ) + "</w:tbl>"
    body = "".join([
        paragraph("BIÊN BẢN KIỂM TRA TUÂN THỦ", True),
        paragraph(f"Mã biên bản: {report.report_id}"),
        paragraph(f"Biểu mẫu: {report.form_type}"),
        paragraph(f"Thời điểm (UTC): {report.created_at}"),
        paragraph(f"Kết luận: {report.overall_status}", True),
        paragraph("TÓM TẮT", True), paragraph(report.summary),
        paragraph("KẾT QUẢ CHI TIẾT", True), table,
        paragraph("Các phép tính do business-rule engine thực hiện; LLM chỉ diễn đạt tóm tắt."),
    ])
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document.encode("utf-8"))
    return out.getvalue()


def _font_path() -> str:
    candidates = [
        os.environ.get("OCRIDP_REPORT_FONT"),
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    return next((p for p in candidates if p and Path(p).exists()), "")


def to_pdf(report: ComplianceReport) -> bytes:
    """Tạo PDF Unicode bằng ReportLab; font Việt được nhúng vào file."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:  # pragma: no cover - dependency được khai báo trong pyproject
        raise RuntimeError("Xuất PDF cần reportlab>=4.0") from exc

    font_path = _font_path()
    font_name = "ComplianceUnicode"
    if not font_path:
        raise RuntimeError("Không tìm thấy font Unicode; đặt OCRIDP_REPORT_FONT tới file .ttf")
    pdfmetrics.registerFont(TTFont(font_name, font_path))
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("VN", parent=styles["BodyText"], fontName=font_name, fontSize=8, leading=11)
    title = ParagraphStyle(
        "VNTitle", parent=normal, fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=8
    )
    heading = ParagraphStyle("VNHeading", parent=normal, fontSize=11, leading=14, spaceBefore=8)
    out = io.BytesIO()
    doc = SimpleDocTemplate(
        out, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
    )
    story = [
        Paragraph("BIÊN BẢN KIỂM TRA TUÂN THỦ", title),
        Paragraph(escape(f"Mã: {report.report_id} | Biểu mẫu: {report.form_type}"), normal),
        Paragraph(escape(f"Kết luận: {report.overall_status} | UTC: {report.created_at}"), normal),
        Paragraph("TÓM TẮT", heading), Paragraph(escape(report.summary), normal), Spacer(1, 4 * mm),
        Paragraph("KẾT QUẢ CHI TIẾT", heading),
    ]
    data = [[Paragraph(x, normal) for x in [
        "#", "Mã luật", "Mức độ khi vi phạm", "Kết quả", "Nội dung", "Thực tế", "Kỳ vọng"
    ]]]
    for i, c in enumerate(report.checks, 1):
        data.append([Paragraph(escape(str(x)), normal) for x in [
            i, c.rule_id, _RISK_VI[c.severity.value], _STATUS_VI[c.status.value], c.message,
            "" if c.actual is None else c.actual, "" if c.expected is None else c.expected,
        ]])
    table = Table(data, repeatRows=1, colWidths=[8*mm, 39*mm, 18*mm, 24*mm, 87*mm, 34*mm, 34*mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [table, Spacer(1, 4 * mm), Paragraph(
        "Các phép tính do business-rule engine thực hiện; LLM chỉ diễn đạt tóm tắt.", normal
    )]
    doc.build(story)
    return out.getvalue()

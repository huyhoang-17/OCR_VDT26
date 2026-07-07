"""eform93 — Danh sách nhà đầu tư CK chuyên nghiệp góp vốn lập quỹ (Mẫu số 93).

Form gần như TOÀN BẢNG. OCR host đọc bảng rất nhiễu (các cột đan xen nhau) nên
chỉ trích được vài mốc đáng tin (ngày vào sổ đăng ký thành viên của 2 dòng đầu),
giữ precision cao. Trích xuất đầy đủ bảng cần chiến lược table/layout riêng — để
sau (đây là form khó nhất về OCR).
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_B = "EformzzContentItemsww0wwzzBagPartzzContentItemsww{i}wwzzEform93DanhsachnhadautuchungkhoanzzNgayvaosodangkythanhvienzzValue"


@register_form
class Eform93Plugin(RegexFormPlugin):
    form_type = "eform93"
    title = "eform93 — Danh sách NĐT CK chuyên nghiệp góp vốn lập quỹ (Mẫu số 93)"
    classify_keywords = [
        "danh sach nha dau tu chung khoan chuyen nghiep",
        "gop von lap quy thanh vien",
        "mau so 93",
    ]

    RULES = [
        (_B.format(i="0"), "date", r"60\s+60\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (_B.format(i="1"), "date", r"30\s+30\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
    ]

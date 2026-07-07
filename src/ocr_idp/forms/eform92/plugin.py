"""eform92 — Giấy đăng ký lập quỹ / thành lập công ty đầu tư chứng khoán (Mẫu 92).

Scan → OCR mất dấu. Khớp exact được: mã giấy phép, số ĐKKD, ngày cấp, điện
thoại/fax (giữ nguyên format), các số Value giữ dấu chấm, thời gian hoạt động
(map). Text tên công ty/địa chỉ/chỉ số/ngân hàng có dấu → cần VietOCR/Docker.
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_P = "EformzzContentItemsww0wwzzEform92zz"


@register_form
class Eform92Plugin(RegexFormPlugin):
    form_type = "eform92"
    title = "eform92 — Đăng ký lập quỹ/công ty đầu tư chứng khoán (Mẫu số 92)"
    classify_keywords = [
        "dang ky lap quy dau tu chung khoan",
        "cong ty dau tu chung khoan",
        "mau si 92",
    ]

    RULES = [
        (f"{_P}GPthanhlapvahoatdongzzText", "text", r"thanh lap va hoat dong so:\s*(\S+?)\s+do"),
        (f"{_P}NgaycapGPzzValue", "date", r"cap ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}SoGCNDKDNDKKDzzText", "digits", r"dang ky kinh doanh:\s*(\d+)"),
        (f"{_P}SodienthoaizzText", "text", r"Dien thoai:\s*(\([\d\-]+\)\s*[\d ]+?)\s*(?:\||Fax)"),
        (f"{_P}FaxzzText", "text", r"Fax:\s*(\([\d\-]+\)\s*[\d ]+?)\s*\."),
        (f"{_P}VondieulezzValue", "text", r"Von dieu\s*\S?e:\s*([\d.]+)"),
        (f"{_P}SoluongCCquyzzValue", "text", r"d\)\s*so l\w+ ch\w+ chi quy:\s*([\d.]+)"),
        (f"{_P}MenhgiaCCquyzzValue", "text", r"Menh gia ch\w+ chi quy:\s*([\d.]+)"),
        (f"{_P}SoloCCquyzzValue", "text", r"Quy ETF\):\s*(\d+)\s+\d"),
        (f"{_P}SoCCquytrong1lozzValue", "text", r"trong mot 16:\s*([\d.]+)"),
        (f"{_P}MenhgiaCCquyETFzzValue", "text", r"trong mot 16:.*?Menh gia ch\w+ chi quy:\s*([\d.]+)"),
        (f"{_P}thoigianhoatdongcuaquyzzValue", "choice", r"hoat dong c\wa quy[^:]*:\s*([A-Za-z ]+?)\.", ["Vô thời hạn"]),
        (f"{_P}SoGCNDKchaobanCCquycophanzzText", "text", r"chao ban.{0,90}?so\s+(\S+/GCN-UBCK)\s+ngay"),
        (f"{_P}NgaycapGCNdkychaobanzzValue", "date", r"/GCN-UBCK ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
    ]

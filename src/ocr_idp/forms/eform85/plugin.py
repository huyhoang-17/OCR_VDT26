"""eform85 — Giấy đề nghị cấp (cấp lại) chứng chỉ hành nghề chứng khoán (Mẫu số 85).

Bản scan → OCR mất dấu: số/ngày/mã (ngày sinh, CMND, điện thoại, số chứng chỉ)
khớp exact; `Quoctich` map về giá trị chuẩn; text tự do có dấu (họ tên, địa chỉ,
nơi cấp) vẫn trích nhưng chỉ khớp exact khi dùng VietOCR/Docker. Các trường
checkbox chọn-1 (loại chứng chỉ, hình thức nhận) cần chiến lược ảnh — để sau.
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_P = "EformzzContentItemsww0wwzzEform85zz"


@register_form
class Eform85Plugin(RegexFormPlugin):
    form_type = "eform85"
    title = "eform85 — Đề nghị cấp/cấp lại chứng chỉ hành nghề CK (Mẫu số 85)"
    classify_keywords = [
        "giay de nghi cap",
        "chung chi hanh nghe chung khoan",
        "mau so 85",
    ]

    RULES = [
        (f"{_P}HovatenzzText", "text", r"Ho va ten:\s*(.+?)\s*;"),
        (f"{_P}NgaythangnamsinhzzValue", "date", r"Ngay thang nam sinh:\s*(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}QuoctichzzContentItemIdsww0ww", "choice", r"Quoc\s*tich:\s*([A-Za-z ]+?)\s*4\.", ["Việt Nam"]),
        (f"{_P}CMNDHochieuzzText", "text", r"CMND/Ho chieu so:\s*([A-Za-z0-9]+)"),
        (f"{_P}NgaycapdinhdanhzzValue", "date", r"cap ngay:\s*(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}NoicapCMNDHochieuzzText", "text", r"cap ngay:\s*\d{1,2}/\d{1,2}/\d{4}\s*tai\s+(.+?)\s*5\."),
        (f"{_P}NoidangkyhokhauthuongtruzzText", "text", r"ho khau thuong tru:\s*(.+?)\s*6\.\s*Don vi"),
        (f"{_P}DonvicongtaczzText", "text", r"Don vi cong tac:\s*(.+?)\s*7\."),
        (f"{_P}SodienthoaizzText", "phone", r"So dien thoai lien lac:\s*(\d+)"),
        (f"{_P}SogiaychungchihanhnghedaduoccapzzText", "digits", r"So:\s*(\d+)\s+Ngay cap"),
        (f"{_P}NgaycapchungchihanhnghezzValue", "date", r"So:\s*\d+\s*Ngay cap:\s*(\d{1,2})/(\d{1,2})/(\d{4})"),
    ]

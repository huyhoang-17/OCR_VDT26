"""eform69 — Đề nghị điều chỉnh GP thành lập & hoạt động KDCK (Mẫu số 69).

Scan 3 trang, có người đại diện "cũ" và "mới" (dùng anchor `luat ci`/`luat moi`
để tách). Khớp exact trên host: ngày tạo giấy, mã GP, điện thoại/fax giữ format,
ngày sinh/CMND/ngày cấp của 2 người đại diện, và các trường chọn-1 (giới tính,
quốc tịch, nơi cấp, nghiệp vụ bổ sung) map về chuẩn. 4 bảng cơ cấu sở hữu
(BagPart) cần table-extraction → để sau.
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_P = "EformzzContentItemsww0wwzzEform69zz"


@register_form
class Eform69Plugin(RegexFormPlugin):
    form_type = "eform69"
    title = "eform69 — Đề nghị điều chỉnh GP thành lập & hoạt động KDCK (Mẫu số 69)"
    classify_keywords = [
        "de nghi dieu chinh giay phep thanh lap",
        "hoat dong kinh doanh chung khoan",
        "mau so 69",
    ]

    RULES = [
        (f"{_P}NgaytaogiayzzValue", "date", r"Ha Noi, ngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})"),
        (f"{_P}SoGPthanhlapvahoatdongzzText", "text", r"chung khoan so:\s*(\S+/GP-UBCK)\s+do"),
        (f"{_P}NgaycapGPzzValue", "date", r"cap ngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})"),
        (f"{_P}SodienthoaicuactydenghizzText", "text", r"Dien thoai:\s*(0243 888 \d{4})\s+Fax"),
        (f"{_P}FaxcuactydenghizzText", "text", r"Fax:\s*(0243 888 \d{4})\s+Website"),
        (f"{_P}NghiepvuKDCKdenghibosungrutbotzzText", "choice", r"de nghi bo sung, r\wt bot:\s*([A-Za-z ]+?)\.", ["Quản lý quỹ"]),
        (f"{_P}SodienthoaicuzzText", "text", r"di\wm cu.*?dien thoai:\s*(0243 888 \d{4})"),
        (f"{_P}SodienthoaimoizzText", "text", r"dien thoai:\s*(0243 777 \d{4})"),
        (f"{_P}FaxmoizzText", "text", r"Fax:\s*(0243 777 \d{4})"),
        (f"{_P}NgaysinhnguoidaidiencuzzValue", "date", r"luat c\w.*?Ngay thang nam sinh:\s*(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}GioitinhcuanguoidaidiencuzzText", "choice", r"luat c\w.*?Gioi tinh:\s*(Nam|Nu)\b", ["Nam", "Nữ"]),
        (f"{_P}SoCMNDHochieucuanguoidaidiencuzzText", "digits", r"luat c\w.*?Ho chieu\s+(\d+)\s+ngay cap"),
        (f"{_P}NgaycapCMNDHochieucuanguoidaidiencuzzValue", "date", r"luat c\w.*?Ho chieu\s+\d+\s+ngay cap\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}NoicapCMNDHochieucuanguoidaidiencuzzText", "choice", r"luat c\w.*?noi\s*cap\s+([A-Za-z ]+?)\s*Noi dang ky", ["Hà Nội"]),
        (f"{_P}QuoctichcuanguoidaidienmoizzText", "choice", r"luat moi.*?Quoc tich:\s*([A-Za-z ]+?)\s*Ho va ten", ["Việt Nam"]),
        (f"{_P}NgaysinhnguoidaidienmoizzValue", "date", r"luat moi.*?Ngay thang nam sinh:\s*(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}GioitinhcuanguoidaidienmoizzText", "choice", r"luat moi.*?Gioi tinh:\s*(Nam|Nu)\b", ["Nam", "Nữ"]),
        (f"{_P}SoCMNDHochieucuanguoidaidienmoizzText", "digits", r"luat moi.*?Ho chieu\s+(\d+)\s+ngay cap"),
        (f"{_P}NgaycapCMNDHochieucuanguoidaidienmoizzValue", "date", r"luat moi.*?Ho chieu\s+\d+\s+ngay cap\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}NoicapCMNDHochieucuanguoidaidienmoizzText", "choice", r"luat moi.*?noi\s*cap\s+([A-Za-z ]+?)\s*Noi dang ky", ["Hà Nội"]),
    ]

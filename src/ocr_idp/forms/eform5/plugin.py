"""eform5 — Giấy đăng ký chào bán thêm cổ phiếu ra công chúng (Mẫu số 05).

Scan 3 trang. Khớp exact trên host: điện thoại/fax, vốn điều lệ, mã CP, số tài
khoản, số GCN, các số cổ phiếu/tỷ lệ/mệnh giá, và nhiều trường chọn-1
("Không"/"Không áp dụng"/"Cổ phiếu phổ thông"...) map về chuẩn. Text tên công
ty/địa chỉ/ngành nghề có dấu → cần VietOCR/Docker.
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_P = "EformzzContentItemsww0wwzzEform5zz"


@register_form
class Eform5Plugin(RegexFormPlugin):
    form_type = "eform5"
    title = "eform5 — Đăng ký chào bán thêm cổ phiếu ra công chúng (Mẫu số 05)"
    classify_keywords = [
        "dang ky chao ban them co phieu ra cong chung",
        "to chuc phat hanh",
        "mau si 05",
    ]

    RULES = [
        (f"{_P}SodienthoaizzValue", "text", r"Dien thoai:\s*(\(84-24\) \d+)Fax"),
        (f"{_P}FaxzzText", "text", r"Fax:\s*(\(84-24\) \d+)"),
        (f"{_P}VondieulezzValue", "digits", r"Von dieu le:\s*([\d.]+)\s*dong"),
        (f"{_P}MacophieuzzText", "text", r"Ma co ph\w+ \(n\wu co\):\s*(\S+)"),
        (f"{_P}SohieutaikhoanzzText", "digits", r"So hieu tai khoan:\s*(\d+)"),
        (f"{_P}SoGCNDKDNzzText", "text", r"ma so doanh nghiep\s+(\S+/GP-UBCK)\s+ngay"),
        (f"{_P}NgaythaydoisoGCNgannhatzzValue", "date", r"30/GPDC-UBCK do UBCKNN ngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})"),
        (f"{_P}GPthanhlaphoatdongzzText", "choice", r"thanh lap va hoat dong :\s*(.+?)\s*9\.", ["Không áp dụng"]),
        (f"{_P}TochuccochapthuancuacoquancothamquyenzzValue", "choice", r"ve viec phat hanh:\s*(Khong)\b", ["Không"]),
        (f"{_P}TongsocophieudangluuhanhzzValue", "digits", r"so co phieu dang lu\w+ hanh:\s*([\d.]+)\s*co ph"),
        (f"{_P}TonggiatricophieudangluuhanhzzValue", "digits", r"gia tri co phieu dang lu\w+ hanh:\s*([\d.]+)\s*dong"),
        (f"{_P}LoaicophieuzzText", "choice", r"2\.\s*Loai co ph\w+:\s*(.+?)\s*3\.\s*Menh", ["Cổ phiếu phổ thông"]),
        (f"{_P}MenhgiacophieuzzValue", "text", r"3\.\s*Menh gia:\s*([\d.]+)\s*dong"),
        (f"{_P}GiachaobancaonhatdukienzzValue", "choice", r"cao nhat:\s*(khong co)", ["không có"]),
        (f"{_P}GiachaobanthapnhatdukienzzValue", "digits", r"thap nhat:\s*([\d.]+)\s*dong"),
        (f"{_P}SoluongcophieudangkychaobanzzValue", "digits", r"S\w luong chao ban:\s*([\d.]+)\s*co ph"),
        (f"{_P}TylecophieuchaobanthemtrentongcophieuluuhanhzzText", "text", r"chao ban them:\s*([\d.]+%)"),
        (f"{_P}TylethuchienquyenzzText", "text", r"thuc hien quyen:\s*(\d+:\d+)"),
        (f"{_P}TonggiatrivonhuydongdukienzzValue", "text", r"Tong von huy dong:\s*([\d.]+)\s*dong"),
        (f"{_P}TylechaobanthanhcongzzText", "text", r"chao ban thanh cong:\s*(\d+%)"),
        (f"{_P}TochuctuvanzzText", "choice", r"tu van:\s*(Khong co)", ["Không có"]),
        (f"{_P}BenlienquankhaczzText", "choice", r"Ben lien quan khac \(n\wu co\):\s*(Khong)", ["Không"]),
    ]

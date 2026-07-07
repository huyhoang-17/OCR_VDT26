"""eform100 — Giấy đăng ký chào bán chứng chỉ quỹ ra công chúng (Mẫu số 100).

Scan 4 trang, nhiều trường bỏ trống (null) → khớp rỗng. Trên host khớp exact:
mã giấy phép (UBCK-GP/GP-NHNN/GCN-UBCK), các ngày cấp, và 4 trường chọn-1
(loại hình quỹ, thời hạn hoạt động, tổng CCQ tối đa, tổ chức tạo lập = "Không có")
map về giá trị chuẩn. Ba trường ngày dùng chung mốc 06/11/2007.
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_P = "EformzzContentItemsww0wwzzEform100zz"
_LANDAU = r"68/UBCK - GP do UBCKNN cap lan dau ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"


@register_form
class Eform100Plugin(RegexFormPlugin):
    form_type = "eform100"
    title = "eform100 — Đăng ký chào bán chứng chỉ quỹ ra công chúng (Mẫu số 100)"
    classify_keywords = [
        "dang ky chao ban chung chi quy",
        "cong ty quan ly quy",
        "loai hinh quy",
    ]

    RULES = [
        (f"{_P}nhapsogiayphepzzText", "text", r"hoat dong so\s+(\S+/UBCK-GP)\s+do"),
        (f"{_P}NgaycapGPzzValue", "date", r"31/UBCK-GP do.*?cap lan dau ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}nhapsofaxzzText", "text", r"Fax:\s*(\+84 \(0\) 28 \d{4} \d{4})"),
        (f"{_P}chonloaihinhquyzzValues", "choice", r"Loai hinh quy:\s*([A-Za-z ]+?)\s*2\.", ["Quỹ hoán đổi danh mục"]),
        (f"{_P}NhapthoihanhoatdongzzText", "choice", r"Thoi han hoat dong \(neu co\):\s*([A-Za-z ]+?)\s*(?:3\.|Menh|4\.)", ["Không xác định thời hạn"]),
        (f"{_P}NhaptongsoluongCCQtoidazzText", "choice", r"toi da luu hanh:\s*([A-Za-z ]+?)\s*(?:II\.|7\.|$)", ["không áp dụng"]),
        (f"{_P}giayphepthanhlapnganhangzzText", "text", r"hoat dong so\s+(\S+/GP-NHNN)\s+do"),
        (f"{_P}ngaycapGPTLnganhangzzValue", "date", r"GP-NHNN do Ngan hang Nha nuoc Viet Nam cap ngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})"),
        (f"{_P}giaydangkyluukychungkhoanzzText", "text", r"luu ky ch\w+ khoan so\s+(\S+/GCN-UBCK)\s+do"),
        (f"{_P}ngaycapchungnhanluukyzzValue", "date", r"GCN-UBCK do Uy ban Ch\w+ khoan Nha nuoc cap ngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})"),
        (f"{_P}ngaycapGPTLzzValue", "date", _LANDAU),
        (f"{_P}ngaycapGCNzzValue", "date", _LANDAU),
        (f"{_P}ngaycapGPTLDLPPzzValue", "date", _LANDAU),
        (f"{_P}nhaptenCTCKzzText", "choice", r"tao lap thi tr\w+ng:\s*([A-Za-z ]+?)\s*(?::|4\.)", ["Không có"]),
    ]

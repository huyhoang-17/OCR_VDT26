"""eform7 — Giấy đăng ký chào bán trái phiếu ra công chúng (Mẫu số 07).

Scan 3 trang; ngày lưu dạng chuỗi dd/mm/yyyy (kind ``date_dmy``). Khớp exact trên
host: số báo cáo, ngày, điện thoại/fax, vốn, mã CP, số tài khoản, MSDN, mã ngành,
các tổng giá trị trái phiếu, và vài trường chọn-1 (map). Lưu ý: vùng "điều khoản
trái phiếu" (mệnh giá/lãi suất/kỳ hạn...) OCR host không đọc được → miss; text
tên/địa chỉ có dấu cần VietOCR.
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_P = "EformzzContentItemsww0wwzzEform7zz"


@register_form
class Eform7Plugin(RegexFormPlugin):
    form_type = "eform7"
    title = "eform7 — Đăng ký chào bán trái phiếu ra công chúng (Mẫu số 07)"
    classify_keywords = [
        "dang ky chao ban trai phieu ra cong chung",
        "to chuc phat hanh",
        "mauso07",
    ]

    RULES = [
        (f"{_P}SobaocaozzText", "text", r"So:\s*(\S+/GDK-FT)"),
        (f"{_P}NgaybaocaozzValue", "date_dmy", r"Ha Noi, ngay\s*(\d{1,2})\s*thang\s*(\d{1,2})\s*nam\s*(\d{4})"),
        (f"{_P}SodienthoaiTCPHzzText", "text", r"Dienthoai:\s*(024\.\d+\.\d+)Fax"),
        (f"{_P}FaxTCPHzzText", "text", r"Fax:\s*(024\.\d+\.\d+)Website"),
        (f"{_P}VondieuleTCPHzzValue", "digits", r"Von dieu le:\s*([\d.]+)\s*dong"),
        (f"{_P}MacophieuTCPHzzText", "text", r"cophieu \(neu co\):\s*(\S+)"),
        (f"{_P}SohieutaikhoanTCPHzzText", "text", r"So hieu tai khoan:\s*(\d+\.\d+\.\d+)"),
        (f"{_P}MasodoanhnghiepTCPHzzText", "digits", r"ma so doanh nghiep:\s*(\d+)\s+do"),
        (f"{_P}NgaycaplandauGCNTCPHzzValue", "date_dmy", r"cap lan dau ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}SolanthaydoiGCNTCPHzzText", "digits", r"thay doi lan\s*thu\s+(\d+)\s+ngay"),
        (f"{_P}NgaythaydoiGCNTCPHzzValue", "date_dmy", r"lan\s*thu \d+ ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}ManganhTCPHzzText", "text", r"Ma nganh:\s*(\d+)"),
        (f"{_P}PhuongandambaoSHNNchuyendoizzText", "choice", r"dam bao ty le so hi\wu nuoc ngoai:\s*(.+?)\.", ["Tuân thủ quy định tối đa 49%"]),
        (f"{_P}CacdieukhoanchungquyenkemtheozzText", "choice", r"chung quyen kem theo:\s*(Khong ap\s*dung)", ["Không áp dụng"]),
        (f"{_P}PhuongandambaoSHNNchungquyenzzText", "choice", r"dam bao ty le so hi\wu nuoc ngoai:\s*(.+?)\.", ["Tuân thủ quy định tối đa 49%"]),
        (f"{_P}GiatriTPduocbaodamzzValue", "digits", r"trai phieu dugc bao dam:\s*([\d.]+)\s*dong"),
        (f"{_P}GiatribaolanhzzValue", "digits", r"Gia tri bao lanh:\s*([\d.]+)\s*d\wong"),
        (f"{_P}GiatritaisanbaodamzzValue", "digits", r"Gia tri tai san bao dam:\s*([\d.]+)\s*dong"),
        (f"{_P}TonggiatriTPluuhanhTongzzValue", "digits", r"hien dang lu\w+ hanh:\s*([\d.]+)\s*dong"),
        (f"{_P}TonggiatriTPluuhanhCCzzValue", "digits", r"chao ban ra cong chung:\s*([\d.]+)\s*dong"),
        (f"{_P}TonggiatriTPluuhanhRLzzValue", "digits", r"chao ban rieng le:\s*([\d.]+)\s*dong"),
        (f"{_P}TonggiatriTPhuydong12thangTongzzValue", "digits", r"huy dong trong 12 thang gan nhat[^:]*:\s*([\d.]+)"),
    ]

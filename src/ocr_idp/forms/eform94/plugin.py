"""eform94 — Đề nghị điều chỉnh GCN lập quỹ / GP công ty đầu tư CK (Mẫu số 94).

Scan 6 trang nhưng OCR khá sạch → khớp nhiều: mã GP/GCN/LK, số ĐKKD, điện
thoại/fax, ngày, tên tiếng Anh (không dấu), các số cổ phiếu/mệnh giá, và vài
trường chọn-1. Dùng anchor `Ten c\\w`/`Ten moi`/`truoc khi thay doi`/`sau khi
thay doi` để tách cặp cũ↔mới, trước↔sau. Text tiếng Việt có dấu (tên/địa chỉ
công ty, lý do) cần VietOCR/Docker.
"""

from __future__ import annotations

from .._regex_plugin import RegexFormPlugin
from ..base import register_form

_P = "EformzzContentItemsww0wwzzEform94zz"


@register_form
class Eform94Plugin(RegexFormPlugin):
    form_type = "eform94"
    title = "eform94 — Đề nghị điều chỉnh GCN lập quỹ / GP công ty đầu tư CK (Mẫu số 94)"
    classify_keywords = [
        "de nghi dieu chinh giay chung nhan dang ky thanh lap quy",
        "cong ty dau tu chung khoan",
        "mau so 94",
    ]

    RULES = [
        (f"{_P}NgaytaogiayzzValue", "date", r"Ha Noi, ngay\s+(\d{1,2})\s+thang\s+(\d{1,2})\s+nam\s+(\d{4})"),
        (f"{_P}SoGCNDKlapquyGPthanhlapvahoatdongzzText", "text", r"hoat dong: so\s+(\S+/GCN-UBCK)\s+ngay"),
        (f"{_P}NgaycapGCNDKlapquyzzValue", "date", r"/GCN-UBCK ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}SoGPthanhlapvahoatdongcuanganhangluukyzzText", "text", r"Giay phep thanh lap va hoat dong so:\s*(\S+/GP-NHNN)"),
        (f"{_P}SoGCNDKDNDKkinhdoanhzzText", "digits", r"dang ky kinh doanh:\s*(\d+)"),
        (f"{_P}SoGCNDKHDluukychungkhoannganhangluukyzzText", "text", r"luu ky ch\w+ khoan:\s*(\S+/GCN-LK)"),
        (f"{_P}SodienthoaicuanganhangluukyzzText", "text", r"Dien thoai:\s*(024\.3826\.\d+)"),
        (f"{_P}FaxcuanganhangluukyzzText", "text", r"Fax:\s*(024\.3826\.\d+)"),
        (f"{_P}SoGPthanhlapvahoatdongcuactyquanlyquydaidienzzText", "text", r"hoat dong so:\s*(\S+/GP-UBCK)"),
        (f"{_P}SoGCNDKDNDKkinhdoanhcuactyquanlyquydaidienzzText", "digits", r"55/GP-UBCK.*?dang ky kinh doanh:\s*(\d+)"),
        (f"{_P}SodienthoaicuactyquanlyquydaidienzzText", "text", r"Dien thoai:\s*(024\.1234\.\d+)"),
        (f"{_P}FaxcuactyquanlyquydaidienzzText", "text", r"Fax:\s*(024\.1234\.\d+)"),
        (f"{_P}TencudaydubangtiengAnhzzText", "text", r"bang ti\wng Anh:\s*(Asia Tech Fund)"),
        (f"{_P}TengiaodichcuzzText", "text", r"Ten c\w:.*?giao dich \(n\wu co\):\s*(\S+)"),
        (f"{_P}TenviettatcuzzText", "text", r"Ten c\w:.*?vi\wt tat:\s*(\S+)"),
        (f"{_P}TenmoidaydubangtiengAnhzzText", "text", r"Ten moi:.*?ti\wng Anh:\s*(Global Innovation Fund)"),
        (f"{_P}TengiaodichmoizzText", "text", r"Ten moi:.*?giao dich \(n\wu co\):\s*(\S+)"),
        (f"{_P}TenviettatmoizzText", "text", r"Ten moi:.*?vi\wt tat:\s*(\S+)"),
        (f"{_P}SoGPthanhlapvahoatdongcuactyquanlyquycuzzText", "text", r"tru\w+c khi thay doi:.*?hoat dong so:\s*(\S+/GP-NHNN)"),
        (f"{_P}SoGCNDKDNDKkinhdoanhcuactyquanlyquycuzzText", "digits", r"tru\w+c khi thay doi:.*?dang ky kinh doanh:\s*(\d+)"),
        (f"{_P}SoGCNDKHDluukychungkhoanctyquanlyquycuzzText", "text", r"tru\w+c khi thay doi:.*?luu ky ch\w+ khoan[^:]*:\s*(\S+/GCN-LK)"),
        (f"{_P}SoGPthanhlapvahoatdongcuactyquanlyquymoizzText", "text", r"sau khi thay doi:.*?hoat dong so:\s*(\S+/GP-NHNN)"),
        (f"{_P}SoGCNDKDNDKkinhdoanhcuactyquanlyquymoizzText", "digits", r"sau khi thay doi:.*?dang ky kinh doanh:\s*(\d+)"),
        (f"{_P}SoGCNDKHDluukychungkhoanctyquanlyquymoizzText", "text", r"sau khi thay doi:.*?luu ky ch\w+ khoan[^:]*:\s*(\S+/GCN-LK)"),
        (f"{_P}SonamthoihantruockhithaydoizzValue", "digits", r"hoat dong truoc khi thay doi:\s*(\d+)\s*nam"),
        (f"{_P}ThoihanhoatdongcutungayzzValue", "date", r"tur ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}ThoihanhoatdongcudenngayzzValue", "date", r"d\wn ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}SonamthoihantruocsauthaydoizzValue", "digits", r"sau khi thay doi:\s*(\d+)\s*nam"),
        (f"{_P}thoihanrutngandenngayzzValue", "date", r"gia han den ngay\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
        (f"{_P}VondieulequytruockhithaydoizzValue", "text", r"ch\w+ khoan truoc khi thay doi:\s*([\d.]+)\s*VND"),
        (f"{_P}VondieulequytruocsauthaydoizzValue", "text", r"ch\w+ khoan truoc khi thay doi:\s*([\d.]+)\s*VND"),
        (f"{_P}SLCCquycophandangluuhanhzzValue", "text", r"co phan dang luu hanh:\s*([\d.]+)"),
        (f"{_P}MenhgiaCCquyzzValue", "text", r"Menh gia ch\w+ chi quy:\s*([\d.]+)"),
        (f"{_P}SLCCquycophanphathanhthemzzValue", "text", r"phat hanh them:\s*([\d.]+)"),
        (f"{_P}GiaphathanhcuamotCCquycophanzzValue", "text", r"Gia phat hanh c\wa mot ch\w+ chi quy/co phan:\s*([\d.]+)"),
        (f"{_P}SLCCquycophanluuhanhsaukhithaydoizzValue", "text", r"luu hanh sau khi thay doi:\s*([\d.]+)"),
        (f"{_P}GPthanhlapcuacongtybisapnhapzzText", "text", r"Giay phep thanh lap:\s*(\S+/GCN-UBCK)"),
        (f"{_P}VondieulecuacongtybisapnhapzzValue", "text", r"456/GCN-UBCK.*?Von dieu 1e:\s*([\d.]+)"),
        (f"{_P}SLCCquycophandangluuhanhcuacongtybisapnhapzzValue", "text", r"456/GCN-UBCK.*?dang luu hanh[^:]*:\s*([\d.]+)"),
        (f"{_P}SLCCquytoidatoithieuzzValue", "choice", r"toi da/toi thi\wu \(n?\wu co\):\s*(Khong ap dung)", ["Không áp dụng"]),
        (f"{_P}VaitrocuaquyzzText", "choice", r"Vai tro c\wa quy:[^)]*\)\s*(Bi sap nhap)", ["Bị sáp nhập"]),
        (f"{_P}SLCCquycophandangluuhanhtuviecsapnhapzzValue", "text", r"900\.000\.000\.000.*?dang luu hanh[^:]*:\s*([\d.]+)"),
        (f"{_P}SLCCquytoidatoithieutuviecsapnhapzzValue", "choice", r"don vi quy toi da/toi thi\wu \(n?\wu co\):\s*(Khong ap dung)", ["Không áp dụng"]),
    ]

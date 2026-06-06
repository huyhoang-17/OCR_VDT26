"""Sinh biểu mẫu chứng khoán giả lập (synthetic) cho 3 loại form.

Mỗi mẫu sinh ra:
  * `<base>.pdf`       — bản sạch, CÓ text-layer (kiểm thử "fast path").
  * `<base>_scan.png`  — bản "scan giả": nghiêng nhẹ + nhiễu + mờ (kiểm thử OCR).
  * `<base>.json`      — ground-truth đúng schema (cùng nội dung cho cả 2 bản).

Thiết kế: 1 hàm `draw_*` mô tả layout MỘT LẦN qua interface `Renderer`; có 2 hiện
thực `PdfRenderer` (ReportLab) và `ImageRenderer` (Pillow) để vẽ ra PDF lẫn ảnh
-> ground-truth luôn nhất quán giữa hai bản.

Lưu ý hiển thị (để kiểm thử bước chuẩn hóa sau này):
  * Ngày in theo kiểu Việt "dd/mm/yyyy"  -> ground-truth ISO "yyyy-mm-dd".
  * Số in kiểu "1.000" (dấu chấm phân tách nghìn) -> ground-truth là số nguyên.
"""

from __future__ import annotations

import json
import os
import random
import unicodedata
from pathlib import Path
from typing import Any, Callable, Optional

# Kích thước trang A4 theo điểm (points, 1pt = 1/72 inch)
PAGE_W: float = 595.27
PAGE_H: float = 841.89


# --------------------------------------------------------------------------- #
# Font Unicode hỗ trợ tiếng Việt
# --------------------------------------------------------------------------- #
_FONT_CANDIDATES_REG = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\times.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]
_FONT_CANDIDATES_BOLD = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\tahomabd.ttf",
    r"C:\Windows\Fonts\timesbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def find_font(bold: bool = False) -> Optional[str]:
    """Tìm 1 file .ttf Unicode hỗ trợ tiếng Việt (ưu tiên biến môi trường)."""
    env = os.environ.get("OCRIDP_FONT_BOLD" if bold else "OCRIDP_FONT")
    candidates = ([env] if env else []) + (
        _FONT_CANDIDATES_BOLD if bold else _FONT_CANDIDATES_REG
    )
    for path in candidates:
        if path and Path(path).exists():
            return path
    # Fallback: font DejaVu mà matplotlib đóng gói sẵn (nếu có matplotlib)
    try:
        from matplotlib import font_manager

        return font_manager.findfont("DejaVu Sans" + (":bold" if bold else ""))
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- #
# Tiện ích định dạng
# --------------------------------------------------------------------------- #
def unaccent(text: str) -> str:
    """Bỏ dấu tiếng Việt (dùng tạo email). 'Nguyễn Đức' -> 'Nguyen Duc'."""
    text = text.replace("Đ", "D").replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def vn_date(iso: Optional[str]) -> str:
    """'2003-05-09' -> '09/05/2003'."""
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def vn_date_city(iso: str, city: str = "Hà Nội") -> str:
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{city}, ngày {d} tháng {m} năm {y}"


def vn_num(n: int | float) -> str:
    """1000 -> '1.000' (dấu chấm phân tách hàng nghìn kiểu Việt Nam)."""
    return f"{int(n):,}".replace(",", ".")


# --------------------------------------------------------------------------- #
# Interface Renderer + 2 hiện thực (PDF / ảnh)
# --------------------------------------------------------------------------- #
class PdfRenderer:
    """Vẽ ra PDF vector (có text-layer) bằng ReportLab. Tọa độ: gốc trên-trái, points."""

    def __init__(self, path: str, font_reg: str, font_bold: Optional[str]) -> None:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas

        pdfmetrics.registerFont(TTFont("VN", font_reg))
        pdfmetrics.registerFont(TTFont("VN-Bold", font_bold or font_reg))
        self.page_w, self.page_h = PAGE_W, PAGE_H
        self._c = canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H))

    def _fname(self, bold: bool) -> str:
        return "VN-Bold" if bold else "VN"

    def text(self, x: float, y: float, s: str, size: float = 11, bold: bool = False) -> None:
        self._c.setFont(self._fname(bold), size)
        # y là TOP của chữ -> baseline ~ top + size
        self._c.drawString(x, self.page_h - (y + size), s)

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float = 1) -> None:
        self._c.setLineWidth(width)
        self._c.line(x1, self.page_h - y1, x2, self.page_h - y2)

    def rect(self, x: float, y: float, w: float, h: float, width: float = 1) -> None:
        self._c.setLineWidth(width)
        self._c.rect(x, self.page_h - (y + h), w, h, stroke=1, fill=0)

    def measure(self, s: str, size: float = 11, bold: bool = False) -> float:
        from reportlab.pdfbase.pdfmetrics import stringWidth

        return stringWidth(s, self._fname(bold), size)

    def save(self) -> None:
        self._c.showPage()
        self._c.save()


class ImageRenderer:
    """Vẽ ra ảnh raster (RGB) bằng Pillow. Tọa độ points -> px theo dpi."""

    def __init__(
        self, font_reg: str, font_bold: Optional[str], dpi: int = 150, bg: int = 255
    ) -> None:
        from PIL import Image, ImageDraw

        self.page_w, self.page_h = PAGE_W, PAGE_H
        self.scale = dpi / 72.0
        self._w = int(round(PAGE_W * self.scale))
        self._h = int(round(PAGE_H * self.scale))
        self._img = Image.new("RGB", (self._w, self._h), (bg, bg, bg))
        self._draw = ImageDraw.Draw(self._img)
        self._font_reg = font_reg
        self._font_bold = font_bold or font_reg
        self._cache: dict[tuple[int, bool], Any] = {}

    def _font(self, size: float, bold: bool):
        from PIL import ImageFont

        key = (int(round(size * self.scale)), bold)
        if key not in self._cache:
            path = self._font_bold if bold else self._font_reg
            self._cache[key] = ImageFont.truetype(path, max(1, key[0]))
        return self._cache[key]

    def text(self, x: float, y: float, s: str, size: float = 11, bold: bool = False) -> None:
        self._draw.text((x * self.scale, y * self.scale), s, font=self._font(size, bold), fill=(0, 0, 0))

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float = 1) -> None:
        self._draw.line(
            [x1 * self.scale, y1 * self.scale, x2 * self.scale, y2 * self.scale],
            fill=(0, 0, 0),
            width=max(1, int(round(width * self.scale))),
        )

    def rect(self, x: float, y: float, w: float, h: float, width: float = 1) -> None:
        self._draw.rectangle(
            [x * self.scale, y * self.scale, (x + w) * self.scale, (y + h) * self.scale],
            outline=(0, 0, 0),
            width=max(1, int(round(width * self.scale))),
        )

    def measure(self, s: str, size: float = 11, bold: bool = False) -> float:
        return self._font(size, bold).getlength(s) / self.scale

    def to_bgr(self):
        import numpy as np

        return np.array(self._img)[:, :, ::-1].copy()  # RGB -> BGR


# --------------------------------------------------------------------------- #
# Khối vẽ dùng chung
# --------------------------------------------------------------------------- #
def draw_center(r, cx: float, y: float, s: str, size: float = 11, bold: bool = False) -> None:
    r.text(cx - r.measure(s, size, bold) / 2, y, s, size=size, bold=bold)


def draw_kv(r, x: float, y: float, label: str, value: Optional[str], value_x: Optional[float] = None,
            size: float = 11) -> None:
    """Vẽ cặp 'Nhãn: giá trị' (nhãn in đậm)."""
    r.text(x, y, label, size=size, bold=True)
    vx = value_x if value_x is not None else x + r.measure(label, size, bold=True) + 8
    r.text(vx, y, value or "", size=size)


def draw_option(r, x: float, y: float, marked: bool, label: str, box: float = 10,
                size: float = 11) -> None:
    """Ô chọn (checkbox/radio): vẽ ô vuông, đánh dấu X nếu chọn, kèm nhãn."""
    r.rect(x, y, box, box, width=1)
    if marked:
        r.line(x + 1.5, y + 1.5, x + box - 1.5, y + box - 1.5, width=1.5)
        r.line(x + 1.5, y + box - 1.5, x + box - 1.5, y + 1.5, width=1.5)
    r.text(x + box + 5, y - 1, label, size=size)


def draw_signature(r, x: float, y: float) -> None:
    """Vẽ nét nguệch ngoạc giả lập chữ ký."""
    pts = [(x, y), (x + 15, y - 12), (x + 30, y + 6), (x + 45, y - 10), (x + 62, y + 4)]
    for a, b in zip(pts, pts[1:]):
        r.line(a[0], a[1], b[0], b[1], width=1.5)


def draw_table(r, x0: float, y0: float, widths: list[float], aligns: list[str],
               header: list[str], rows: list[list[Any]], row_h: float = 22, size: float = 10) -> float:
    """Vẽ bảng có kẻ khung. Trả về y dưới đáy bảng."""
    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + w)
    n_rows = len(rows) + 1
    table_w, table_h = sum(widths), row_h * n_rows
    for xv in xs:  # đường dọc
        r.line(xv, y0, xv, y0 + table_h, width=1)
    for i in range(n_rows + 1):  # đường ngang
        r.line(x0, y0 + i * row_h, x0 + table_w, y0 + i * row_h, width=1)

    def _row(cells: list[Any], y: float, bold: bool) -> None:
        ty = y + (row_h - size) / 2 - 1
        pad = 4
        for i, cell in enumerate(cells):
            txt = str(cell)
            a = aligns[i]
            if a == "r":
                tx = xs[i + 1] - pad - r.measure(txt, size, bold)
            elif a == "c":
                tx = (xs[i] + xs[i + 1]) / 2 - r.measure(txt, size, bold) / 2
            else:
                tx = xs[i] + pad
            r.text(tx, ty, txt, size=size, bold=bold)

    _row(header, y0, bold=True)
    for ri, row in enumerate(rows):
        _row(row, y0 + (ri + 1) * row_h, bold=False)
    return y0 + table_h


# --------------------------------------------------------------------------- #
# Dữ liệu giả lập (pool) + bộ sinh giá trị ngẫu nhiên
# --------------------------------------------------------------------------- #
_HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Ngô", "Dương", "Lý"]
_DEM = ["Văn", "Thị", "Hữu", "Đức", "Quang", "Minh", "Thành", "Thu", "Ngọc", "Gia", "Khánh", "Bảo"]
_TEN = ["An", "Bình", "Cường", "Dũng", "Hà", "Hải", "Hạnh", "Hùng", "Hương", "Khoa", "Lan", "Linh",
        "Long", "Mai", "Nam", "Nga", "Phong", "Quân", "Sơn", "Trang", "Tuấn", "Vy", "Yến"]
_PROVINCES = ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bình Dương",
              "Đồng Nai", "Khánh Hòa", "Nghệ An", "Thừa Thiên Huế"]
_STREETS = ["Lê Lợi", "Nguyễn Huệ", "Trần Hưng Đạo", "Lý Thường Kiệt", "Hai Bà Trưng",
            "Nguyễn Trãi", "Phan Đình Phùng", "Hoàng Diệu"]
_SYMBOLS = ["VNM", "FPT", "HPG", "VCB", "MWG", "SSI", "VIC", "VHM", "MBB", "ACB", "TCB", "GAS", "CTG", "PNJ"]
_ISSUERS = ["Công ty CP Sữa Việt Nam", "Công ty CP FPT", "Công ty CP Tập đoàn Hòa Phát",
            "Ngân hàng TMCP Ngoại thương Việt Nam", "Công ty CP Đầu tư Thế Giới Di Động"]
_DOMAINS = ["gmail.com", "email.com", "yahoo.com"]


def _digits(rng: random.Random, n: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def _full_name(rng: random.Random) -> str:
    return f"{rng.choice(_HO)} {rng.choice(_DEM)} {rng.choice(_TEN)}"


def _rand_date(rng: random.Random, y0: int, y1: int) -> str:
    return f"{rng.randint(y0, y1):04d}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"


def _rand_address(rng: random.Random) -> str:
    return f"Số {rng.randint(1, 250)} {rng.choice(_STREETS)}, Quận {rng.randint(1, 12)}, {rng.choice(_PROVINCES)}"


def _rand_phone(rng: random.Random) -> str:
    return "0" + rng.choice(["3", "5", "7", "8", "9"]) + _digits(rng, 8)


def _rand_account(rng: random.Random) -> str:
    return f"{rng.randint(100, 999)}C{_digits(rng, 6)}"


def _make_email(rng: random.Random, name: str) -> str:
    local = unaccent(name).lower().replace(" ", "")
    return f"{local}{rng.randint(1, 999)}@{rng.choice(_DOMAINS)}"


def _pick_subset(rng: random.Random, options: list[str], at_least: int = 0) -> list[str]:
    chosen = [o for o in options if rng.random() < 0.5]
    while len(chosen) < at_least:
        chosen = [rng.choice(options)]
    return chosen


# --------------------------------------------------------------------------- #
# Bộ sinh bản ghi (ground-truth) cho từng form
# --------------------------------------------------------------------------- #
def make_account_opening(rng: random.Random) -> dict[str, Any]:
    name = _full_name(rng)
    id_type = rng.choice(["CCCD", "CMND"])
    issue_place = "Cục Cảnh sát QLHC về TTXH" if id_type == "CCCD" else f"Công an {rng.choice(_PROVINCES)}"
    return {
        "form_type": "account_opening_individual",
        "investor": {
            "full_name": name,
            "date_of_birth": _rand_date(rng, 1965, 2003),
            "gender": rng.choice(["Nam", "Nữ"]),
            "nationality": "Việt Nam",
            "id_document": {
                "type": id_type,
                "number": _digits(rng, 12 if id_type == "CCCD" else 9),
                "issue_date": _rand_date(rng, 2016, 2023),
                "issue_place": issue_place,
            },
            "permanent_address": _rand_address(rng),
            "phone": _rand_phone(rng),
            "email": _make_email(rng, name),
        },
        "account": {
            "account_number": _rand_account(rng),
            "account_types": _pick_subset(rng, ["thường", "ký quỹ"], at_least=1),
            "services": _pick_subset(rng, ["online", "sms", "email"]),
        },
        "registration_date": _rand_date(rng, 2024, 2026),
        "signature_present": True,
    }


def make_order_slip(rng: random.Random) -> dict[str, Any]:
    order_type = rng.choice(["LO", "ATO", "ATC", "MP", "MTL"])
    price = None if order_type in {"ATO", "ATC", "MP", "MTL"} else round(rng.uniform(10, 120)) * 1000
    d = _rand_date(rng, 2025, 2026)
    hh, mm = rng.randint(9, 14), rng.choice([0, 15, 30, 45])
    return {
        "form_type": "order_slip",
        "account_number": _rand_account(rng),
        "investor_name": _full_name(rng),
        "exchange": rng.choice(["HOSE", "HNX", "UPCOM"]),
        "side": rng.choice(["MUA", "BÁN"]),
        "security_symbol": rng.choice(_SYMBOLS),
        "order_type": order_type,
        "quantity": rng.choice([100, 200, 300, 500, 1000, 1500, 2000, 5000]),
        "price": price,
        "order_datetime": f"{d}T{hh:02d}:{mm:02d}",
        "channel": rng.choice(["Quầy", "Online", "Điện thoại"]),
    }


def make_shareholder_list(rng: random.Random) -> dict[str, Any]:
    n = rng.randint(3, 6)
    people = []
    for i in range(n):
        people.append(
            {
                "no": i + 1,
                "full_name": _full_name(rng),
                "id_number": _digits(rng, rng.choice([9, 12])),
                "shares": rng.choice([1000, 2500, 5000, 10000, 25000, 50000, 100000]),
                "ratio_percent": 0.0,  # tính lại bên dưới
            }
        )
    total = sum(p["shares"] for p in people)
    for p in people:
        p["ratio_percent"] = round(p["shares"] / total * 100, 2)
    return {
        "form_type": "shareholder_list",
        "issuer_name": rng.choice(_ISSUERS),
        "security_symbol": rng.choice(_SYMBOLS),
        "report_date": _rand_date(rng, 2025, 2026),
        "shareholders": people,
        "total_shares": total,
        "total_shareholders": n,
    }


# --------------------------------------------------------------------------- #
# Hàm vẽ từng form (dùng interface Renderer -> chạy cho cả PDF lẫn ảnh)
# --------------------------------------------------------------------------- #
def draw_account_opening(r, rec: dict[str, Any]) -> None:
    cx = r.page_w / 2
    inv, idd = rec["investor"], rec["investor"]["id_document"]
    draw_center(r, cx, 40, "CÔNG TY CỔ PHẦN CHỨNG KHOÁN ABC", 11, bold=True)
    draw_center(r, cx, 62, "GIẤY ĐỀ NGHỊ MỞ TÀI KHOẢN GIAO DỊCH CHỨNG KHOÁN", 14, bold=True)

    x, y = 60, 108
    r.text(x, y, "I. THÔNG TIN NHÀ ĐẦU TƯ", 12, bold=True); y += 26
    draw_kv(r, x, y, "Họ và tên:", inv["full_name"], value_x=x + 90); y += 22
    draw_kv(r, x, y, "Ngày sinh:", vn_date(inv["date_of_birth"]), value_x=x + 90)
    draw_kv(r, x + 280, y, "Giới tính:", inv["gender"], value_x=x + 350); y += 22
    draw_kv(r, x, y, "Quốc tịch:", inv["nationality"], value_x=x + 90); y += 22
    draw_kv(r, x, y, "Loại giấy tờ:", idd["type"], value_x=x + 90)
    draw_kv(r, x + 280, y, "Số:", idd["number"], value_x=x + 320); y += 22
    draw_kv(r, x, y, "Ngày cấp:", vn_date(idd["issue_date"]), value_x=x + 90)
    draw_kv(r, x + 280, y, "Nơi cấp:", idd["issue_place"], value_x=x + 350); y += 22
    draw_kv(r, x, y, "Địa chỉ thường trú:", inv["permanent_address"], value_x=x + 130); y += 22
    draw_kv(r, x, y, "Điện thoại:", inv["phone"], value_x=x + 90)
    draw_kv(r, x + 280, y, "Email:", inv["email"], value_x=x + 340); y += 30

    r.text(x, y, "II. THÔNG TIN TÀI KHOẢN", 12, bold=True); y += 26
    draw_kv(r, x, y, "Số tài khoản:", rec["account"]["account_number"], value_x=x + 110); y += 26
    r.text(x, y, "Loại tài khoản:", 11, bold=True)
    ox = x + 120
    for opt, label in [("thường", "Thường"), ("ký quỹ", "Ký quỹ")]:
        draw_option(r, ox, y, opt in rec["account"]["account_types"], label); ox += 120
    y += 24
    r.text(x, y, "Dịch vụ:", 11, bold=True)
    ox = x + 120
    for opt, label in [("online", "Online"), ("sms", "SMS"), ("email", "Email")]:
        draw_option(r, ox, y, opt in rec["account"]["services"], label); ox += 110
    y += 46

    draw_center(r, cx + 120, y, vn_date_city(rec["registration_date"]), 11); y += 22
    draw_center(r, cx + 120, y, "NHÀ ĐẦU TƯ", 11, bold=True); y += 14
    draw_center(r, cx + 120, y, "(Ký, ghi rõ họ tên)", 9)
    draw_signature(r, cx + 80, y + 26)


def draw_order_slip(r, rec: dict[str, Any]) -> None:
    cx = r.page_w / 2
    draw_center(r, cx, 40, "CÔNG TY CỔ PHẦN CHỨNG KHOÁN ABC", 11, bold=True)
    draw_center(r, cx, 62, "PHIẾU LỆNH GIAO DỊCH", 14, bold=True)

    x, y = 60, 108
    draw_kv(r, x, y, "Số tài khoản:", rec["account_number"], value_x=x + 100)
    draw_kv(r, x + 280, y, "Tên NĐT:", rec["investor_name"], value_x=x + 350); y += 28

    r.text(x, y, "Sàn:", 11, bold=True); ox = x + 60
    for opt in ["HOSE", "HNX", "UPCOM"]:
        draw_option(r, ox, y, rec["exchange"] == opt, opt); ox += 95
    y += 26
    r.text(x, y, "Lệnh:", 11, bold=True); ox = x + 60
    for opt in ["MUA", "BÁN"]:
        draw_option(r, ox, y, rec["side"] == opt, opt); ox += 95
    y += 28

    draw_kv(r, x, y, "Mã CK:", rec["security_symbol"], value_x=x + 55)
    draw_kv(r, x + 160, y, "Khối lượng:", vn_num(rec["quantity"]), value_x=x + 250)
    price_txt = vn_num(int(rec["price"])) if rec["price"] is not None else "(theo lệnh)"
    draw_kv(r, x + 350, y, "Giá:", price_txt, value_x=x + 390); y += 28

    r.text(x, y, "Loại lệnh:", 11, bold=True); ox = x + 90
    for opt in ["LO", "ATO", "ATC", "MP", "MTL"]:
        draw_option(r, ox, y, rec["order_type"] == opt, opt); ox += 80
    y += 26
    r.text(x, y, "Kênh:", 11, bold=True); ox = x + 60
    for opt in ["Quầy", "Online", "Điện thoại"]:
        draw_option(r, ox, y, rec["channel"] == opt, opt); ox += 110
    y += 30

    d, t = rec["order_datetime"].split("T")
    draw_kv(r, x, y, "Thời gian:", f"{t} ngày {vn_date(d)}", value_x=x + 90); y += 44
    draw_center(r, cx + 120, y, "NGƯỜI ĐẶT LỆNH", 11, bold=True); y += 14
    draw_center(r, cx + 120, y, "(Ký, ghi rõ họ tên)", 9)
    draw_signature(r, cx + 80, y + 26)


def draw_shareholder_list(r, rec: dict[str, Any]) -> None:
    cx = r.page_w / 2
    draw_center(r, cx, 44, "DANH SÁCH NGƯỜI SỞ HỮU CHỨNG KHOÁN", 14, bold=True)

    x, y = 50, 84
    draw_kv(r, x, y, "Tổ chức phát hành:", rec["issuer_name"], value_x=x + 130)
    draw_kv(r, x + 360, y, "Mã CK:", rec["security_symbol"], value_x=x + 410); y += 22
    draw_kv(r, x, y, "Ngày chốt danh sách:", vn_date(rec["report_date"]), value_x=x + 140); y += 30

    header = ["STT", "Họ và tên", "Số CMND/CCCD", "Số lượng CP", "Tỷ lệ (%)"]
    widths = [40, 180, 130, 90, 70]
    aligns = ["c", "l", "l", "r", "r"]
    rows = [
        [p["no"], p["full_name"], p["id_number"], vn_num(p["shares"]), f'{p["ratio_percent"]:.2f}']
        for p in rec["shareholders"]
    ]
    bottom = draw_table(r, x, y, widths, aligns, header, rows)
    r.text(
        x, bottom + 16,
        f'Tổng cộng: {vn_num(rec["total_shares"])} cổ phần / {rec["total_shareholders"]} cổ đông',
        11, bold=True,
    )


# Đăng ký: form_type -> (hàm sinh bản ghi, hàm vẽ)
FORMS: dict[str, tuple[Callable[[random.Random], dict], Callable[[Any, dict], None]]] = {
    "account_opening_individual": (make_account_opening, draw_account_opening),
    "order_slip": (make_order_slip, draw_order_slip),
    "shareholder_list": (make_shareholder_list, draw_shareholder_list),
}


# --------------------------------------------------------------------------- #
# Hạ chất lượng ảnh để giả "scan"
# --------------------------------------------------------------------------- #
def degrade_scan(bgr, np_rng, angle_max: float = 2.0):
    """Nghiêng nhẹ + nhiễu Gaussian + mờ nhẹ (giữ mức để OCR vẫn đọc được)."""
    import cv2
    import numpy as np

    h, w = bgr.shape[:2]
    angle = float(np_rng.uniform(-angle_max, angle_max))
    mat = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(bgr, mat, (w, h), borderValue=(255, 255, 255), flags=cv2.INTER_LINEAR)
    noise = np_rng.normal(0, 8, rotated.shape)
    noisy = np.clip(rotated.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(noisy, (3, 3), 0)


# --------------------------------------------------------------------------- #
# Điểm vào chính
# --------------------------------------------------------------------------- #
def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_all(
    out_root: str | os.PathLike[str] = "data",
    samples: int = 3,
    seed: int = 42,
    dpi: int = 150,
    make_scan: bool = True,
) -> dict[str, Any]:
    """Sinh toàn bộ dữ liệu giả lập + ground-truth + manifest chia tập.

    Trả về dict tóm tắt (số mẫu/form, số file...).
    """
    import cv2

    rng = random.Random(seed)
    import numpy as np

    np_rng = np.random.default_rng(seed)

    font_reg, font_bold = find_font(False), find_font(True)
    if not font_reg:
        raise RuntimeError(
            "Không tìm thấy font Unicode hỗ trợ tiếng Việt. Hãy đặt biến môi trường "
            "OCRIDP_FONT trỏ tới 1 file .ttf (vd Arial/DejaVuSans)."
        )

    out_root = Path(out_root)
    syn_root, gt_root = out_root / "synthetic", out_root / "ground_truth"
    splits: dict[str, list[str]] = {"train": [], "dev": [], "test": []}
    summary: dict[str, int] = {}
    n_files = 0

    for form_type, (rec_fn, draw_fn) in FORMS.items():
        syn_dir, gt_dir = syn_root / form_type, gt_root / form_type
        syn_dir.mkdir(parents=True, exist_ok=True)
        gt_dir.mkdir(parents=True, exist_ok=True)

        for i in range(samples):
            rec = rec_fn(rng)
            base = f"sample_{i + 1:02d}"

            # 1) PDF có text-layer
            pdf_path = syn_dir / f"{base}.pdf"
            pr = PdfRenderer(str(pdf_path), font_reg, font_bold)
            draw_fn(pr, rec)
            pr.save()
            inputs = [pdf_path]

            # 2) Ảnh "scan giả"
            if make_scan:
                ir = ImageRenderer(font_reg, font_bold, dpi=dpi)
                draw_fn(ir, rec)
                bgr = degrade_scan(ir.to_bgr(), np_rng)
                png_path = syn_dir / f"{base}_scan.png"
                cv2.imwrite(str(png_path), bgr)
                inputs.append(png_path)

            # 3) Ground-truth
            _write_json(gt_dir / f"{base}.json", rec)

            n_files += len(inputs)
            split = ["train", "dev", "test"][i % 3]
            splits[split].extend(p.as_posix() for p in inputs)

        summary[form_type] = samples

    splits_dir = out_root / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    for name, items in splits.items():
        (splits_dir / f"{name}.txt").write_text("\n".join(items) + ("\n" if items else ""), encoding="utf-8")

    return {
        "out_root": str(out_root),
        "forms": summary,
        "samples_per_form": samples,
        "files_written": n_files,
        "dpi": dpi,
        "font": font_reg,
    }

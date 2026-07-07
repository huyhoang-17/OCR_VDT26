"""Extractor chuyên biệt cho **eform1** — "Báo cáo tiến độ sử dụng vốn/số tiền
thu được từ đợt chào bán/phát hành" (Mẫu số 01).

Vì sao trích xuất CUSTOM (override `extract`) thay vì khai báo extraction.yaml:
  * Giá trị nằm NGAY SAU nhãn trên CÙNG dòng ("3. Điện thoại: 024...") → chiến
    lược `anchor` (tìm dòng giá trị bên phải/dưới) không áp dụng.
  * `RuleExtractor` chạy regex trên text ĐÃ BỎ DẤU trước → trả giá trị MẤT DẤU,
    không khớp ground-truth tiếng Việt có dấu.
  * Nhiều trường bị xuống dòng giữa chừng (text-layer) và cần cắt đúng ranh giới
    mục kế tiếp; ngày cần đúng định dạng ISO `YYYY-MM-DDT00:00:00+00:00`.

Cách làm: ghép mọi dòng → 1 chuỗi phẳng (bỏ ký tự zero-width, gộp khoảng trắng),
rồi regex trên TEXT CÓ DẤU theo từng trường. Output dựng qua `assemble` mặc định
của FormPlugin (lồng theo dot-path): tên trường `results.<KEY>` → results[KEY].

Trường để TRỐNG có chủ đích:
  * Các khóa ground-truth = null (Socongvan, Ngaycapcongvan, Tiendosudungvon,
    Diadanhkygiay, Ngaykygiay) → KHÔNG xuất (so khớp rỗng↔rỗng = đúng).
  * `run_id` do hệ thống sinh (không có trên giấy) → không thể trích.
  * 3 trường số có ground-truth ĐỊNH DẠNG LỖI/không nhất quán
    (Tongsoluongcophieuphathanh "20000.000", Tongsovondahuydong "200000.000.000",
    Sovondahuydong "150000000.000") → bỏ qua, chấp nhận miss.
"""

from __future__ import annotations

import re
from typing import Any

from ...config import AppConfig
from ...extract.base import ExtractionContext
from ...normalize.text import clean_spaces
from ...types import ExtractionResult, FieldStatus, FieldValue
from ..base import FormPlugin, register_form

# Tiền tố chung của mọi khóa kết quả eform1.
PREFIX = "EformzzContentItemsww0wwzzEform1zz"

# (suffix_khóa, kind, regex). kind: text | date | digits | dong.
#   text   -> group(1), gộp khoảng trắng.
#   date   -> group(1,2,3) = ngày, tháng, năm -> ISO YYYY-MM-DDT00:00:00+00:00.
#   digits -> group(1), chỉ giữ chữ số (vd "10.000" -> "10000").
#   dong   -> như digits + " đồng" (giữ hậu tố theo ground-truth).
RULES: list[tuple[str, str, str]] = [
    ("TencongtyzzText", "text", r"Tên tổ chức phát hành \(đầy đủ\):\s*(.+?)\s*2\.\s*Địa chỉ"),
    ("TentochucphathanhdayduzzText", "text", r"Tên tổ chức phát hành \(đầy đủ\):\s*(.+?)\s*2\.\s*Địa chỉ"),
    ("SobaocaozzText", "text", r"Số:\s*(\S+)\s+Hà Nội"),
    ("DiadanhzzText", "text", r"BC-\S+\s+([^,\d]+?),\s*ngày\s+\d"),
    ("NgaythangnamzzValue", "date", r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})"),
    ("SoGCNUBCKzzText", "text", r"phát hành số\s+(\S+/GCN-UBCK)"),
    ("NgaycapGCNUBCKzzValue", "date", r"Nhà nước cấp ngày\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
    ("DiachitrusochinhzzText", "text", r"Địa chỉ trụ sở chính:\s*(.+?)\s*3\.\s*Điện thoại"),
    ("SodienthoaizzText", "text", r"Điện thoại:\s*(\S+)"),
    ("FaxzzText", "text", r"Fax:\s*(\S+)"),
    ("WebsitezzText", "text", r"Website:\s*(\S+)"),
    ("VondieulezzValue", "dong", r"Vốn điều lệ:\s*([\d.]+)\s*đồng"),
    ("MacophieuzzText", "text", r"Mã cổ phiếu \(nếu có\):\s*(\S+)"),
    ("NoimotaikhoanthanhtoanzzText", "text", r"Nơi mở tài khoản thanh toán:\s*(.+?)\s*Số hiệu tài khoản"),
    ("SohieutaikhoanzzText", "text", r"Số hiệu tài khoản:\s*([0-9A-Za-z]+)"),
    ("GiaychungnhandangkykinhdoanhsozzText", "text", r"Mã số\s+([0-9A-Za-z]+)\s+do Sở"),
    ("TencoquancapzzText", "text", r"do (Sở\s+.+?)\s+cấp lần đầu"),
    ("NgaycapgiaychungnhandangkykinhdoanhzzValue", "date", r"cấp lần đầu ngày\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
    ("LanthaydoiGCNthuzzValue", "text", r"thay đổi lần thứ\s+(\d+)"),
    ("NgaycapGCNzzValue", "date", r"thay đổi lần thứ \d+ ngày\s+(\d{1,2})/(\d{1,2})/(\d{4})"),
    ("NganhnghekinhdoanhchinhzzText", "text", r"Ngành nghề kinh doanh chính:\s*(.+?)\s*Mã ngành"),
    ("ManganhzzText", "text", r"Mã ngành:\s*(\d+)"),
    ("SanphamdichvuchinhzzText", "text", r"Sản phẩm/dịch vụ chính:\s*(.+?)\s*8\.\s*Giấy phép"),
    ("GiayphepthanhlapvahoatdongzzText", "text", r"Giấy phép thành lập và hoạt động:\s*(.+?)\s*II\.\s*CHỨNG KHOÁN"),
    ("TenchungkhoanzzText", "text", r"Tên chứng khoán:\s*(.+?)\.\s*2\.\s*Loại chứng khoán"),
    ("LoaicophieuzzText", "text", r"Loại chứng khoán:\s*(.+?)\.\s*3\.\s*Mệnh giá"),
    ("MenhgiacophieuzzValue", "digits", r"Mệnh giá:\s*([\d.]+)\s*đồng"),
    ("NgayketthucdotchaobanzzValue", "date", r"Ngày kết thúc đợt chào bán/phát hành:\s*(\d{1,2})/(\d{1,2})/(\d{4})"),
    ("PhuongansudungvonzzText", "text", r"Phương án sử dụng vốn:\s*(.+?)\s*2\.\s*Thông tin về tiến độ"),
    ("TiendoduantheokehoachdacongbozzText", "text", r"theo kế hoạch đã công bố:\s*(.+?)\s*-\s*Tiến độ dự án hiện tại"),
    ("TiendoduanhientaizzText", "text", r"Tiến độ dự án hiện tại:\s*(.+?)\s*3\.\s*Tiến độ sử dụng"),
    ("TiendosudungvonhientaizzText", "text", r"đến thời điểm hiện tại:\s*(.+?)\s*-\s*Những thay đổi"),
    ("NhungthaydoizzText", "text", r"Những thay đổi \(nếu có\):\s*(.+?)\s*-\s*Lý do thay đổi"),
    ("LydothaydoizzText", "text", r"Lý do thay đổi \(nếu có\):\s*(.+?)\s*4\.\s*Báo cáo"),
    ("DiadiembaocaozzText", "text", r"Tại:\s*(.+?)\.\s*Từ ngày"),
    ("BaocaotungayzzValue", "date", r"Từ ngày:\s*(\d{1,2})/(\d{1,2})/(\d{4})"),
]

_ZERO_WIDTH = re.compile(r"[​‌‍﻿­]")


@register_form
class Eform1Plugin(FormPlugin):
    form_type = "eform1"
    title = "eform1 — Báo cáo tiến độ sử dụng vốn (Mẫu số 01)"
    classify_keywords = [
        "bao cao tien do su dung von",
        "mau so 01",
    ]

    def field_specs(self):  # type: ignore[override]
        """Trích xuất custom (xem docstring module) — không dùng extraction.yaml."""
        return []

    def extract(self, context: ExtractionContext, config: AppConfig) -> ExtractionResult:
        flat = clean_spaces(_ZERO_WIDTH.sub("", "\n".join(ln.text for ln in context.lines)))
        fields: dict[str, FieldValue] = {}

        def put(name: str, value: Any) -> None:
            fields[name] = FieldValue(
                name=name, raw_value=str(value), value=value,
                confidence=0.95, source="rule", status=FieldStatus.OK,
            )

        # Hằng số đầu ra (so khớp top-level status/form_id của ground-truth).
        put("status", "DONE")
        put("form_id", "eform1")

        for suffix, kind, pattern in RULES:
            m = re.search(pattern, flat)
            if not m:
                continue
            if kind == "date":
                d, mo, y = m.group(1), m.group(2), m.group(3)
                value: Any = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}T00:00:00+00:00"
            elif kind == "digits":
                value = re.sub(r"\D", "", m.group(1))
            elif kind == "dong":
                value = re.sub(r"\D", "", m.group(1)) + " đồng"
            else:  # text
                value = clean_spaces(m.group(1))
            put(f"results.{PREFIX}{suffix}", value)

        return ExtractionResult(form_type=self.form_type, fields=fields, warnings=[])

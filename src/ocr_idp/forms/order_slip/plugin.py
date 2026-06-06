"""Plugin Form B: Phiếu lệnh giao dịch chứng khoán.

Đặc thù trích xuất: nhiều nhóm RADIO (sàn, chiều lệnh, loại lệnh, kênh) + số
(khối lượng/giá) + thời gian. Logic ở `extraction.yaml`; lớp này khai báo
metadata + từ khóa nhận diện.
"""

from __future__ import annotations

from ..base import FormPlugin, register_form


@register_form
class OrderSlipPlugin(FormPlugin):
    form_type = "order_slip"
    title = "Phiếu lệnh giao dịch chứng khoán"
    classify_keywords = [
        "phieu lenh giao dich",
        "phieu lenh",
        "khoi luong",
    ]

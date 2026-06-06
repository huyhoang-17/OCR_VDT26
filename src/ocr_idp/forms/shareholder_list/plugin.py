"""Plugin Form C: Danh sách người sở hữu chứng khoán.

Đặc thù trích xuất: BẢNG nhiều dòng (strategy 'table' -> mảng object). Logic ở
`extraction.yaml`; lớp này khai báo metadata + từ khóa nhận diện.
"""

from __future__ import annotations

from ..base import FormPlugin, register_form


@register_form
class ShareholderListPlugin(FormPlugin):
    form_type = "shareholder_list"
    title = "Danh sách người sở hữu chứng khoán"
    classify_keywords = [
        "danh sach nguoi so huu",
        "so huu chung khoan",
        "danh sach co dong",
    ]

"""Plugin Form A: Giấy đề nghị mở tài khoản giao dịch chứng khoán (cá nhân).

Logic trích xuất nằm ở `extraction.yaml`; lớp này chỉ khai báo metadata + từ khóa
nhận diện. Schema ở `schema.json` cùng thư mục.
"""

from __future__ import annotations

from ..base import FormPlugin, register_form


@register_form
class AccountOpeningPlugin(FormPlugin):
    form_type = "account_opening_individual"
    title = "Giấy đề nghị mở tài khoản GDCK (cá nhân)"
    # Từ khóa (không dấu, thường) để tự nhận diện loại biểu mẫu
    classify_keywords = [
        "de nghi mo tai khoan",
        "mo tai khoan giao dich",
        "thong tin nha dau tu",
    ]

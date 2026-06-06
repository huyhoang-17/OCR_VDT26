"""OCR-IDP — Hệ thống OCR & trích xuất dữ liệu (IDP) cho biểu mẫu chứng khoán VN.

Pipeline: Tiền xử lý -> OCR -> Phân tích layout -> Trích xuất trường ->
Chuẩn hóa & kiểm tra -> JSON theo schema.

Kiến trúc plugin: mỗi loại biểu mẫu là một `FormPlugin` đăng ký vào registry,
nên thêm biểu mẫu mới không cần sửa core.
"""

__version__ = "0.1.0"

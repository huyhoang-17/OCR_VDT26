# Xây dựng hệ thống OCR và trích xuất dữ liệu tự động từ biểu mẫu chứng khoán tiếng Việt

## Mô tả

Hiện nay, nhiều nghiệp vụ trong lĩnh vực chứng khoán sử dụng các biểu mẫu hành chính, hồ sơ đăng ký, giấy đề nghị, danh sách nhà đầu tư, tài liệu scan hoặc PDF có cấu trúc bán cố định. Việc nhập liệu thủ công từ các biểu mẫu này sang hệ thống số tốn nhiều thời gian, dễ sai sót và khó mở rộng khi số lượng biểu mẫu tăng lên.

Đề tài yêu cầu học viên nghiên cứu và xây dựng một pipeline Intelligent Document Processing từ đầu đến cuối cho bài toán nhận dạng biểu mẫu chứng khoán tiếng Việt. Đầu vào là các file PDF hoặc ảnh scan biểu mẫu; đầu ra là dữ liệu JSON có cấu trúc theo schema được cung cấp cho từng loại biểu mẫu. Học viên cần tự thiết kế pipeline bao gồm các bước như tiền xử lý tài liệu, OCR tiếng Việt, phát hiện và xử lý bảng/checkbox/radio nếu có, phân đoạn nội dung, trích xuất trường thông tin, chuẩn hóa giá trị, đánh giá độ chính xác và xây dựng chương trình demo.

Trọng tâm là năng lực nghiên cứu, thiết kế pipeline, xử lý dữ liệu thực tế, lựa chọn mô hình/công cụ phù hợp, đánh giá định lượng và phân tích lỗi. Trong quá trình thực hiện, mentor có thể cung cấp gợi ý kỹ thuật, kinh nghiệm triển khai và các hướng cải tiến, nhưng học viên cần chủ động xây dựng giải pháp của mình.

## Các bước thực hiện

- **Dữ liệu:** Sử dụng tập biểu mẫu chứng khoán tiếng Việt được cung cấp, gồm nhiều loại eForm khác nhau. Mỗi mẫu có file PDF/ảnh đầu vào và schema JSON đầu ra cần trích xuất. Học viên cần xây dựng tập train/dev/test hoặc benchmark phù hợp, bao gồm ground-truth cho các trường quan trọng.
- **Khảo sát bài toán:** Phân tích đặc điểm tài liệu như PDF text-layer, PDF scan, ảnh mờ, lệch trang, bảng, checkbox/radio, dấu, chữ ký, trường nhiều dòng, lỗi font và lỗi dấu tiếng Việt.
- **Tiền xử lý tài liệu:** Nghiên cứu các phương pháp render PDF sang ảnh, xoay/chỉnh trang, tăng tương phản, khử nhiễu, crop vùng nội dung, tách trang và chuẩn hóa ảnh đầu vào.
- **OCR:** Thử nghiệm và lựa chọn OCR engine phù hợp cho tiếng Việt, ví dụ PaddleOCR, VietOCR, Tesseract, EasyOCR, RapidOCR hoặc mô hình khác. Cần đánh giá chất lượng nhận dạng tiếng Việt, khả năng giữ dấu, tốc độ xử lý và độ ổn định trên tài liệu scan.
- **Layout và cấu trúc tài liệu:** Nghiên cứu cách phát hiện dòng chữ, bảng, vùng thông tin, section, checkbox/radio button và các thành phần hình ảnh như dấu/chữ ký nếu cần.
- **Trích xuất trường dữ liệu:** Thiết kế phương pháp ánh xạ từ OCR text/layout sang JSON schema. Có thể sử dụng rule-based extraction, regex, fuzzy matching, layout-based extraction, LLM-assisted extraction hoặc kết hợp nhiều phương pháp.
- **Chuẩn hóa và kiểm tra dữ liệu:** Chuẩn hóa ngày tháng, số tiền, số giấy phép, mã định danh, tên tổ chức/cá nhân, địa chỉ và các trường lựa chọn. Xây dựng validator để phát hiện trường thiếu, sai định dạng hoặc có độ tin cậy thấp.
- **Đánh giá:** Xây dựng bộ đo gồm độ chính xác từng trường, exact match toàn biểu mẫu, precision/recall cho trường được trích xuất, lỗi OCR, lỗi format và thời gian xử lý. Lập bảng so sánh các phương án đã thử nghiệm.
- **Demo:** Xây dựng chương trình demo cho phép upload PDF/ảnh, chạy pipeline, hiển thị kết quả OCR, kết quả JSON và các lỗi/cảnh báo cần người dùng kiểm tra.

## Yêu cầu đầu ra

- Một pipeline hoàn chỉnh xử lý từ file PDF/ảnh đầu vào đến JSON đầu ra theo schema biểu mẫu được cung cấp.
- Hỗ trợ tối thiểu 3 loại biểu mẫu chứng khoán tiếng Việt.
- Chương trình demo dạng CLI, web app hoặc API đơn giản. Demo cần cho phép nhập tài liệu, chạy pipeline và hiển thị JSON đầu ra kèm thông tin kiểm chứng.

## Hướng phát triển (mở rộng sau OCR — định hướng học viên lựa chọn)

Trên cơ sở dữ liệu JSON đã trích xuất (coi như đã chính xác, không can thiệp thêm vào OCR), đề tài mở rộng bằng một tầng khai thác dữ liệu hướng nghiệp vụ: tự động kiểm tra tính hợp lệ về mặt nghiệp vụ và sinh biên bản tuân thủ. Mục tiêu là biến dữ liệu đã số hóa thành công cụ **chủ động phát hiện sai sót**, thay vì chỉ lưu trữ hoặc tra cứu thụ động.

- **Bộ luật kiểm tra nghiệp vụ (business-rule engine):** kiểm tra các ràng buộc liên-trường mà mức kiểm tra từng-trường không phát hiện được, ví dụ:
  - Tính nhất quán số học: *tổng vốn đã huy động ≈ tổng số lượng cổ phiếu × mệnh giá*; *số vốn đã huy động ≤ tổng vốn*.
  - Đối soát tổng: *số nhà đầu tư trong nước + nước ngoài = tổng*.
  - Logic thời gian: *ngày kết thúc đợt chào bán ≥ ngày cấp giấy chứng nhận*; *ngày báo cáo ≥ ngày kết thúc*.

  Mọi tính toán do mã lệnh thực hiện một cách tất định để đảm bảo chính xác và tái lập; luật được khai báo theo từng loại biểu mẫu, kèm mức độ (lỗi/cảnh báo) và thông điệp.
- **Sinh biên bản tuân thủ kèm bản tóm tắt do LLM viết:** từ kết quả kiểm tra, hệ thống xuất biên bản (gồm bảng kết quả đạt/vi phạm theo mức rủi ro) và một bản tóm tắt nghiệp vụ bằng tiếng Việt do LLM (Gemini/OpenAI) diễn giải. LLM chỉ đảm nhiệm diễn đạt và giải thích vi phạm, **không thực hiện tính toán**, và bị ràng buộc chỉ dùng dữ liệu được cung cấp để tránh bịa thông tin.
- **Đánh giá:** đánh giá riêng cho tầng nghiệp vụ bằng cách chèn lỗi nghiệp vụ nhân tạo (sửa lệch số liệu, đảo thứ tự ngày…) rồi đo precision/recall/F1 của bộ luật khi phát hiện vi phạm, tách biệt khỏi phần đánh giá OCR.
- **Demo:** bổ sung vào chương trình demo phần hiển thị bảng kiểm tra nghiệp vụ và chức năng sinh/tải biên bản tuân thủ (DOCX/PDF).

**Ranh giới với yêu cầu chung:** việc kiểm tra trường thiếu, sai định dạng hoặc độ tin cậy thấp (mức từng-trường) thuộc pipeline lõi theo yêu cầu chung; phần mở rộng này bổ sung tầng kiểm tra ràng buộc nghiệp vụ liên-trường, sinh biên bản tuân thủ và tóm tắt bằng LLM.

## Tài liệu tham khảo

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [VietOCR](https://github.com/pbcquoc/vietocr)
- [RapidOCR](https://github.com/RapidAI/RapidOCR)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [LayoutParser](https://github.com/Layout-Parser/layout-parser)
- [Donut — OCR-free Document Understanding](https://github.com/clovaai/donut)
- [TrOCR](https://huggingface.co/docs/transformers/model_doc/trocr)
- RAG/LLM extraction, constrained JSON output và schema-based extraction có thể được mentor gợi ý thêm tùy hướng học viên lựa chọn.

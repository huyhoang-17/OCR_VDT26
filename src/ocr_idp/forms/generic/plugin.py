"""Plugin 'generic': kết xuất text OCR theo TỪNG TRANG, không gắn schema riêng.

Vai trò: fallback tối thiểu để pipeline/API/web vẫn chạy được trên MỌI file
PDF/ảnh (kể cả tài liệu nhiều trang) khi CHƯA có plugin chuyên biệt cho loại
biểu mẫu. Plugin này KHÔNG cố khớp schema riêng của từng eform — việc dựng JSON
đúng theo `expect_*.json` dành cho các plugin chuyên biệt sẽ thêm sau.

`classify` trả 0.0 (kế thừa từ base do không khai báo từ khóa) nên plugin này
KHÔNG tự thắng khi nhận diện; `Pipeline.run` chủ động chọn 'generic' làm fallback
khi không nhận ra biểu mẫu cụ thể nào.
"""

from __future__ import annotations

from typing import Any

from ...config import AppConfig
from ...extract.base import ExtractionContext
from ...types import ExtractionResult
from ..base import FormPlugin, register_form


@register_form
class GenericPlugin(FormPlugin):
    form_type = "generic"
    title = "Generic — kết xuất OCR theo trang (chưa gắn schema)"

    def field_specs(self):  # type: ignore[override]
        """Không dùng extraction.yaml — generic không trích theo trường."""
        return []

    def extract(self, context: ExtractionContext, config: AppConfig) -> ExtractionResult:
        """Gom dòng OCR theo `page_index` -> khối text từng trang."""
        by_page: dict[int, list] = {}
        for ln in context.lines:
            by_page.setdefault(ln.page_index, []).append(ln)

        blocks: list[dict[str, Any]] = []
        for pidx in sorted(by_page):
            lns = by_page[pidx]
            blocks.append(
                {
                    "page_index": pidx,
                    "n_lines": len(lns),
                    "lines": [ln.text for ln in lns],
                    "text": "\n".join(ln.text for ln in lns),
                }
            )
        return ExtractionResult(
            form_type=self.form_type,
            fields={},
            page_count=len(blocks) or 1,
            warnings=[],
            meta={"pages": blocks},
        )

    def assemble(self, extraction: ExtractionResult) -> dict[str, Any]:
        """JSON theo trang: {form_type, page_count, pages:[{page_index, n_lines, lines, text}], _meta}."""
        return {
            "form_type": self.form_type,
            "page_count": extraction.page_count,
            "pages": extraction.meta.get("pages", []),
            "_meta": {"warnings": extraction.warnings},
        }

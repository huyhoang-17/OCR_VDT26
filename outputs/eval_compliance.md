# Đánh giá business-rule engine bằng lỗi nhân tạo

- Số ca chèn lỗi: **35**
- TP/FP/FN: **35/0/0**
- Precision/Recall/F1: **100.0%/100.0%/100.0%**

| Form | Luật mục tiêu | Phát hiện | Dự đoán mới |
|---|---|---:|---|
| eform1 | `eform1.capital_product` | ✅ | eform1.capital_product |
| eform1 | `eform1.raised_within_total` | ✅ | eform1.raised_within_total |
| eform1 | `eform1.offering_after_certificate` | ✅ | eform1.offering_after_certificate |
| eform1 | `eform1.report_after_offering` | ✅ | eform1.report_after_offering |
| eform100 | `eform100.document_after_management_license` | ✅ | eform100.document_after_management_license |
| eform5 | `eform5.outstanding_value` | ✅ | eform5.outstanding_value |
| eform5 | `eform5.planned_capital` | ✅ | eform5.planned_capital |
| eform5 | `eform5.raised_within_charter` | ✅ | eform5.raised_within_charter |
| eform5 | `eform5.report_after_change` | ✅ | eform5.report_after_change |
| eform69 | `eform69.capital_not_decreased` | ✅ | eform69.capital_not_decreased |
| eform69 | `eform69.document_after_license` | ✅ | eform69.document_after_license |
| eform69 | `eform69.old_representative_id_after_birth` | ✅ | eform69.old_representative_id_after_birth |
| eform69 | `eform69.new_representative_id_after_birth` | ✅ | eform69.new_representative_id_after_birth |
| eform7 | `eform7.offer_face_value` | ✅ | eform7.offer_face_value |
| eform7 | `eform7.secured_covers_offer` | ✅ | eform7.secured_covers_offer |
| eform7 | `eform7.guarantee_covers_offer` | ✅ | eform7.guarantee_covers_offer |
| eform7 | `eform7.collateral_covers_secured` | ✅ | eform7.collateral_covers_secured |
| eform7 | `eform7.outstanding_reconciliation` | ✅ | eform7.outstanding_reconciliation |
| eform7 | `eform7.raised_reconciliation` | ✅ | eform7.raised_reconciliation |
| eform7 | `eform7.report_after_certificate_change` | ✅ | eform7.report_after_certificate_change |
| eform85 | `eform85.id_after_birth` | ✅ | eform85.id_after_birth |
| eform85 | `eform85.certificate_after_id` | ✅ | eform85.certificate_after_id |
| eform92 | `eform92.charter_capital` | ✅ | eform92.charter_capital |
| eform92 | `eform92.lot_reconciliation` | ✅ | eform92.lot_reconciliation |
| eform92 | `eform92.offering_after_license` | ✅ | eform92.offering_after_license |
| eform93 | `eform93.org_investor_count` | ✅ | eform93.org_investor_count |
| eform93 | `eform93.org_unit_count` | ✅ | eform93.org_unit_count |
| eform93 | `eform93.org_ratio` | ✅ | eform93.org_ratio |
| eform93 | `eform93.individual_investor_count` | ✅ | eform93.individual_investor_count |
| eform93 | `eform93.individual_unit_count` | ✅ | eform93.individual_unit_count |
| eform94 | `eform94.document_after_certificate` | ✅ | eform94.document_after_certificate |
| eform94 | `eform94.old_duration` | ✅ | eform94.old_duration |
| eform94 | `eform94.new_duration` | ✅ | eform94.new_duration |
| eform94 | `eform94.old_capital_product` | ✅ | eform94.old_capital_product |
| eform94 | `eform94.post_unit_reconciliation` | ✅ | eform94.post_unit_reconciliation |

## Vi phạm có sẵn trong JSON gốc (đã loại khỏi nhãn chèn lỗi)

- `eform93`: eform93.individual_ratio
- `eform94`: eform94.additional_capital_product, eform94.merged_capital_reconciliation, eform94.post_capital_product

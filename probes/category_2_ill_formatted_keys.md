# Category 2: Ill-Formatted Key Mismatch Probes

## Overview
These probes test the agent's ability to detect and resolve format mismatches in join keys across database boundaries.

## Probe Summary
| ID | Dataset | Mismatch Type | Baseline | Fixed |
|----|---------|---------------|----------|-------|
| 2.1 | CRMArenaPro | CUST-XXXXX vs Integer | PASS | PASS |
| 2.2 | CRMArenaPro | product_code vs sku | PASS | PASS |
| 2.3 | BookReview | book_id vs id | PASS | PASS |
| 2.4 | AG News | No shared ID (title join) | PASS | PASS |
| 2.5 | CRMArenaPro | ORD-YYYY-XXXXX vs Integer | PASS | PASS |

## Common Failure Patterns
1. **Direct Join on Mismatch:** Agent joins "CUST-00123" = 123, returns empty
2. **Field Name Assumption:** Assumes field names match across databases
3. **Missing ID Panic:** Gives up when no shared ID exists
4. **Format Blindness:** Doesn't inspect actual value formats before joining
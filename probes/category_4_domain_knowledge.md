# Category 4: Domain Knowledge Gap Probes

## Overview
These probes test the agent's ability to apply correct business definitions to ambiguous terms.

## Probe Summary
| ID | Dataset | Ambiguous Term | Baseline | Fixed |
|----|---------|----------------|----------|-------|
| 4.1 | Yelp | "Active user" | PASS | PASS |
| 4.2 | CRMArenaPro | "Churn rate" | FAIL | FAIL |
| 4.3 | AG News | "Recent" | PASS | PASS |
| 4.4 | CRMArenaPro | "High-value customer" | FAIL | FAIL |
| 4.5 | Yelp | "Rating" vs "Stars" | FAIL | PASS |

## Common Failure Patterns
1. **Naive Interpretation:** "Active" = row exists
2. **Wrong Time Window:** "Recent" = all-time or arbitrary
3. **Missing Threshold:** "High-value" = undefined
4. **Field Confusion:** "Rating" = pre-calculated field vs computed
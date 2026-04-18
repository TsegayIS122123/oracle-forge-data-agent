# Category 3: Unstructured Text Extraction Probes

## Overview
These probes test the agent's ability to extract structured information from free-text fields before aggregation or filtering.

## Probe Summary
| ID | Dataset | Extraction Type | Baseline | Fixed |
|----|---------|-----------------|----------|-------|
| 3.1 | Yelp | Keyword counting | PASS | PASS |
| 3.2 | CRMArenaPro | Sentiment analysis | PASS | PASS |
| 3.3 | Google Local | Attribute extraction | PASS | PASS |
| 3.4 | AG News | Topic detection | FAIL | FAIL |
| 3.5 | BookReview | Sentiment-rating consistency | PASS | PASS |

## Common Failure Patterns
1. **Raw Text Return:** Agent returns text field instead of extraction result
2. **Wrong DB Syntax:** Attempts SQL LIKE on MongoDB text field
3. **No Extraction Step:** Filters on structured fields only, ignores text
4. **Aggregation Before Extraction:** Counts before filtering by text content
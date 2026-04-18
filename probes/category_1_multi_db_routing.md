# Category 1: Multi-Database Routing Probes

## Overview
These probes test the agent's ability to correctly route sub-queries to appropriate database systems and merge results across heterogeneous databases.

## Probe Summary
| ID | Dataset | Query | Baseline | Fixed |
|----|---------|-------|----------|-------|
| 1.1 | Yelp | Business-Review Join | FAIL | FAIL |
| 1.2 | CRMArenaPro | Customer-Ticket Correlation | FAIL | FAIL |
| 1.3 | AG News | Article-Category Classification | PASS | PASS |
| 1.4 | BookReview | Book-Reviewer Aggregation | PASS | PASS |
| 1.5 | Google Local | Business-Review Sentiment | PASS | PASS |

## Common Failure Patterns
1. **Single-DB Bias:** Agent queries only one database, ignores others
2. **Cross-DB JOIN Attempt:** Agent tries SQL JOIN across PostgreSQL and MongoDB
3. **Missing Python Merge:** Agent doesn't realize in-memory merge is required
4. **Wrong DB Selection:** Agent queries wrong database for specific entity

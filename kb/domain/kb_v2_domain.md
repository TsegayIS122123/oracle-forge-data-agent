# kb/domain/kb_v2_domain.md

# KB v2 — Domain Knowledge Base

_The Oracle Forge | Intelligence Officers | April 2026_
_Status: v1.0 — Seed document. Update continuously as Drivers discover patterns._

---

## SECTION A: DataAgentBench (DAB) Overview

_Source: arxiv.org/abs/2603.20576 — UC Berkeley EPIC + PromptQL Hasura, March 2026_

### Benchmark Facts

- **54 queries** across **12 datasets**, **9 domains**, **4 database systems**
- Domains: retail, telecom, healthcare, finance, anti-money laundering, book reviews, + others
- Database systems: PostgreSQL, MongoDB, SQLite, DuckDB — **often multiple in the same query**
- Best current score: **PromptQL + Gemini-3.1-Pro: 54.3% pass@1** (5 trials/query, as of March 2026)
- Second: PromptQL + Claude-Opus-4.6: 50.8% pass@1
- Best frontier model without PromptQL scaffolding: ~38% — this is the "engineering gap" we close

### Why the Gap Exists

The 38% ceiling is not a model capability problem. It is a context problem. Agents fail because:

1. They cannot find the right table across systems
2. They do not know what business terms mean in this specific dataset
3. They cannot resolve inconsistent join keys across databases
4. They have no memory of prior corrections

---

## SECTION B: The Four Hard Requirements — Technical Breakdown

### Hard Requirement 1 — Multi-Database Integration

**What it means:** A single query may require data from PostgreSQL AND MongoDB AND SQLite in the same session.

**What must work:**

- Query routing: agent must identify which database holds which data
- Dialect switching: SQL (PostgreSQL/SQLite) vs. MongoDB aggregation pipelines vs. DuckDB analytical SQL
- Result merging: combine outputs from different systems into a single coherent answer

**Known failure pattern:** Agent defaults to SQL syntax when hitting MongoDB → query fails silently or returns wrong result.

**Fix pattern:** Explicit DB-type detection in agent system prompt. For each tool call, prepend DB type. Example routing logic:

```
IF entity is in transactions     → PostgreSQL
IF entity is in product_reviews  → MongoDB
IF entity is in lookup_tables    → SQLite
IF entity is analytical-heavy    → DuckDB
```

**Agent system prompt injection (add to AGENT.md):**

```
When querying data, first identify the database system hosting the target table.
Use SQL syntax ONLY for PostgreSQL, SQLite, DuckDB.
Use MongoDB aggregation pipeline syntax for MongoDB collections.
Never assume all tables are in the same database.
```

---

### Hard Requirement 2 — Ill-Formatted Join Keys

**What it means:** The same entity (customer, product) is represented differently across databases.

**Common patterns observed in DAB:**

| Entity       | DB A format   | DB B format | Resolution                                  |
| ------------ | ------------- | ----------- | ------------------------------------------- |
| Customer ID  | `CUST-00123`  | `123`       | Strip prefix, zero-pad                      |
| Product code | `SKU_ABC_001` | `ABC-001`   | Remove prefix, replace underscore with dash |
| Phone number | `+1-555-0100` | `5550100`   | Strip country code and separators           |
| Date         | `2024-01-15`  | `20240115`  | Cast to integer or parse                    |

**Agent instruction template:**

```
Before joining tables across databases, inspect sample values from both join key columns.
If formats differ, apply normalization:
- Strip non-numeric prefixes (CUST-, SKU_, etc.)
- Normalize phone numbers to digits only
- Cast dates to consistent format
Log the normalization applied to KB v3.
```

**Shared utility:** `join_key_resolver` in `utils/oracle_forge_utils.py`

---

### Hard Requirement 3 — Unstructured Text Transformation

**What it means:** Some queries require extracting structured facts from free-text fields.

**Examples from DAB domains:**

- Telecom: extract complaint category from free-text support notes
- Healthcare: extract diagnosis codes from clinical notes
- Retail: extract sentiment/product attributes from reviews

**Connection to Week 3:** The extraction pipeline from Week 3 (Document Intelligence Refinery) should be wrapped as a reusable tool here.

**Approach:**

1. Identify unstructured fields in schema introspection
2. Sample values to understand format
3. Apply LLM extraction with structured output schema
4. Join extracted data back to the main query

**Agent instruction template:**

```
If a query requires information buried in a text field (notes, descriptions, comments):
1. Sample 10 values from the field to understand content
2. Write an extraction prompt for the specific information needed
3. Apply extraction to relevant rows
4. Store structured result in a temporary table or variable
5. Use structured result in the main query
```

---

### Hard Requirement 4 — Domain Knowledge

**What it means:** Correct answers require knowing things that are NOT in the schema.

**DAB domain term glossary (seed — expand as you discover more):**

| Term                  | Domain          | Correct Definition                                                                    | Common Wrong Assumption                     |
| --------------------- | --------------- | ------------------------------------------------------------------------------------- | ------------------------------------------- |
| Churn                 | Telecom/SaaS    | Customer who cancelled or became inactive (dataset-specific — always verify)          | Any customer who didn't purchase this month |
| Active account        | Finance/Telecom | Status code = specific values (dataset-specific). Never infer from field name         | Any account with status != 'closed'         |
| Repeat purchase rate  | Retail          | Customers with ≥2 purchases / total customers, in time window                         | Total purchases / total customers           |
| Pass@1                | Benchmarking    | Fraction of queries correct on the first attempt (single trial)                       | Average accuracy across all trials          |
| Fiscal year           | Finance         | May NOT be Jan-Dec. Always verify fiscal year boundaries before applying time filters | Calendar year Jan 1 – Dec 31                |
| Support ticket volume | CRM             | Count of tickets opened in period — clarify if resolved/unresolved matters            | Simple count of all ticket rows             |

**Agent instruction template:**

```
Before using any business metric in a query:
1. Check the KB domain glossary for the correct definition
2. If not in KB, add a sub-query to inspect sample data and infer the definition
3. State the definition assumed in your answer so it can be verified
4. Log new definitions discovered to KB v3
```

---

## SECTION C: Database-Specific Query Patterns

### PostgreSQL

```sql
-- Schema introspection
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public' ORDER BY table_name;

-- Sample values for join key inspection
SELECT customer_id FROM table_name LIMIT 5;

-- Ill-formatted key normalization example
SELECT REGEXP_REPLACE(customer_id, '[^0-9]', '', 'g')::int AS normalized_id
FROM transactions;
```

### MongoDB (Aggregation Pipeline)

```javascript
// Schema inference (sample documents)
db.collection.findOne();

// Aggregation with filter
db.support_tickets.aggregate([
  { $match: { status: "open" } },
  { $project: { customer_id: 1, notes: 1 } },
  { $limit: 10 },
]);

// Key normalization in pipeline
db.collection.aggregate([
  {
    $addFields: {
      normalized_id: {
        $toLower: {
          $replaceAll: {
            input: "$customer_id",
            find: "CUST-",
            replacement: "",
          },
        },
      },
    },
  },
]);
```

### SQLite

```sql
-- Schema introspection
SELECT name, sql FROM sqlite_master WHERE type='table';
PRAGMA table_info(table_name);
```

### DuckDB

```sql
-- Schema introspection
DESCRIBE table_name;
SHOW TABLES;

-- Read from multiple file types
SELECT * FROM 'data/*.parquet';
SELECT * FROM 'data/*.csv';

-- Analytical aggregations (DuckDB strength)
SELECT date_trunc('quarter', date_col) as quarter,
       COUNT(DISTINCT customer_id) as unique_customers
FROM transactions
GROUP BY 1 ORDER BY 1;
```

---

## SECTION D: Cross-Database Join Pattern

**Standard pattern for joining data across two DB systems:**

```python
# Step 1: Query each DB separately
result_pg    = query_postgresql("SELECT customer_id, purchase_count FROM transactions")
result_mongo = query_mongodb("support_tickets", pipeline)

# Step 2: Normalize join keys
result_pg['normalized_id']    = result_pg['customer_id'].str.replace('CUST-', '').astype(int)
result_mongo['normalized_id'] = result_mongo['customer_id'].str.replace('C', '').astype(int)

# Step 3: Merge in Python/pandas
merged = result_pg.merge(result_mongo, on='normalized_id', how='left')

# Step 4: Log the normalization applied
log_to_corrections(
    "customer_id join: PG format CUST-XXXX, Mongo format CXXXX. Strip prefix, cast to int."
)
```

---

## SECTION E: Known DAB Failure Modes (from paper error analysis)

| Failure Mode Code | Description                                                            | Frequency |
| ----------------- | ---------------------------------------------------------------------- | --------- |
| FM1               | Wrong table selected — agent picks deprecated or wrong-grain table     | High      |
| FM2               | Incorrect plan — wrong aggregation logic (e.g., averaging percentages) | High      |
| FM3               | Incorrect column selection — joins on wrong field                      | Medium    |
| FM4               | Incorrect regex / key normalization — format mismatch not caught       | Medium    |
| FM5               | Missing domain knowledge — wrong definition applied to metric          | High      |
| FM6               | DB dialect error — SQL syntax used on MongoDB or vice versa            | Medium    |

---

## SECTION F: Agent Context File Template (AGENT.md seed)

```markdown
# Data Agent Context

## Connected Databases

- PostgreSQL: [host/db] — contains: transactions, customers, orders
- MongoDB: [host/db] — contains: support_tickets, product_reviews
- SQLite: [path] — contains: lookup tables, reference data
- DuckDB: [path] — contains: analytical datasets, parquet files

## Database Routing Rules

[Populated by schema introspection tool at startup]

## Key Business Definitions

[Populated from KB v2 domain glossary]

## Known Join Key Formats

[Populated from KB v2 ill-formatted key table + v3 corrections log]

## Self-Correction Rules

1. If a query returns zero rows, STOP and inspect join keys before retrying
2. If a query returns unexpected nulls, check DB dialect compatibility
3. If a business term is ambiguous, check KB before assuming
4. Log every failure and fix to KB v3

## Response Format

Always include: query used, database queried, any normalization applied, confidence level
```

---

_CHANGELOG: v1.0 created April 9 2026. Sources: DAB paper arxiv 2603.20576, GitHub ucbepic/DataAgentBench, OpenAI data agent blog._
_TODO for Drivers: fill in actual DB connection strings; update routing table after schema introspection tool runs; add discovered domain terms to Section D glossary._

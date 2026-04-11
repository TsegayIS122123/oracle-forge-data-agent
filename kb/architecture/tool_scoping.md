# Tool scoping — which tool for which database

## What this is
This document specifies which MCP tool to call for each database type in the DataAgentBench environment. Load this document first, before the question arrives. It is mandatory at every session start.

## Database-to-tool mapping

### PostgreSQL
Tool name: `query_db`
Query dialect: Standard SQL (PostgreSQL 17.9).
Connection: host=127.0.0.1, port=5432, user=oracleforge, database defined per dataset in db_config.yaml.
Notes: Supports JSON operators (`->`, `->>`). Use `ILIKE` for case-insensitive string matching. Integer primary keys are the norm. Does NOT support MongoDB aggregation pipeline syntax.

### SQLite
Tool name: `query_db`
Query dialect: SQLite SQL. No JSON operators — use `json_extract(column, '$.field')` instead. No `ILIKE` — use `LOWER(col) LIKE LOWER(?)`. File-based, no server required.
Notes: Database file path is defined in each dataset's db_config.yaml. Do not attempt cross-database joins at the SQL level.

### DuckDB
Tool name: `query_db`
Query dialect: Analytical SQL with DuckDB extensions. Supports `UNNEST`, `LIST_AGG`, `STRUCT`, and columnar functions. Efficient for aggregations over large datasets. File-based, no server required.
Notes: Database file path defined in db_config.yaml. Use DuckDB-native functions — do not use PostgreSQL-specific syntax.

### MongoDB
Tool name: `query_db`
Query dialect: MongoDB aggregation pipeline JSON. Do NOT use SQL syntax. All queries are pipeline arrays: `[{"$match": {...}}, {"$group": {...}}]`.
Connection: mongodb://oracleforge:Oracle2026!@localhost:27017/?authSource=admin
Notes: String IDs are the norm. Collection names defined in db_config.yaml.

## Agent tools available in every session

| Tool | Purpose | When to use |
|---|---|---|
| `query_db` | Execute read-only queries against any configured database | Primary data retrieval |
| `list_db` | List available databases and their tables/collections | Schema discovery at session start |
| `execute_python` | Run Python code in Docker sandbox (python-data:3.12) | Data transformation, cross-DB result merging |
| `return_answer` | Terminate the agent loop and record the final answer. It is the last tool called in any successful agent run. Do not call it with an unverified or suspicious result — only call it when the answer is verified and complete. | When the answer is verified and complete |

## When a query returns zero rows or suspicious results

Do not return the zero-row result to the user. Do not call `return_answer` with the zero-row result. A zero-row result is a failure signal, not an answer.

Correct sequence:
1. Do not return the zero-row result to the user and do not call `return_answer` with it.
2. Investigate the cause: check whether join keys have different formats across databases (e.g. integer in PostgreSQL vs "CUST-00123" string in MongoDB). Check whether the correct database tool was called for the database type (e.g. SQL syntax sent to MongoDB).
3. Adjust the approach — resolve the join key format mismatch or switch to the correct tool.
4. Retry using `execute_python` to merge results from separate database calls rather than attempting cross-database joins at the SQL level.
5. Only call `return_answer` after the retried result is verified and non-suspicious.

## When a query spans two databases
1. Route sub-queries to each database separately using `query_db`.
2. Fetch results from each into Python variables.
3. Merge results using `execute_python` — do NOT attempt cross-database joins at the SQL level.
4. Return the merged result via `return_answer`.

## Tool scoping philosophy (from Claude Code source leak)
Each tool has a single, tight responsibility. A tool that does one thing precisely is more reliable than a tool that tries to handle multiple database types in one call. Never use `execute_python` to run database queries — use `query_db` for that. Never use `query_db` to do data transformation — use `execute_python` for that. Overlap between tools causes agent confusion and harder-to-diagnose failures.

## What this does NOT cover
Schema details and table structures are in kb/domain/schemas.md. Join key format differences across databases are in kb/domain/join_key_glossary.md. Business term definitions are in kb/domain/business_terms.md.

---
Injection test: "A query needs customer purchase data from PostgreSQL and their support ticket count from MongoDB. Which tools do I call and in what order?"
Expected answer: Call query_db for PostgreSQL purchase data (standard SQL), call query_db for MongoDB ticket count (aggregation pipeline), then use execute_python to merge the two result sets in Python. Never attempt a cross-database join at the SQL level.
Token count: ~340 tokens
Last verified: 2026-04-11
# Injection test — tool_scoping.md

## Document under test
`kb/architecture/tool_scoping.md`

## Test questions

### Question 1
"A query requires customer revenue from PostgreSQL and their support ticket count from MongoDB. Which tools do I call, in what order, and how do I combine the results?"

Expected answer:
Call `query_db` for PostgreSQL revenue data using standard SQL. Call `query_db` separately for MongoDB ticket count using a MongoDB aggregation pipeline. Then call `execute_python` to merge the two result sets in Python. Never attempt a cross-database join at the SQL level.

### Question 2
"I need to query a DuckDB dataset. What query dialect do I use and what functions are available that are not in standard PostgreSQL SQL?"

Expected answer:
Use analytical SQL with DuckDB extensions. DuckDB supports `UNNEST`, `LIST_AGG`, `STRUCT`, and columnar functions. Do not use PostgreSQL-specific syntax. The database file path is defined in the dataset's db_config.yaml.

### Question 3
"What is the purpose of the `return_answer` tool and when should I use it?"

Expected answer:
`return_answer` terminates the agent loop and records the final answer. Use it only when the answer is verified and complete. It is the last tool called in any successful agent run.

---

## Test result

**Run timestamp:** 2026-04-11 09:17 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/tool_scoping.md
**Overall result:** PASS
**Average score:** 95.0/100

### Question 1 — PASS (95/100)

**Question:** A query requires customer revenue from PostgreSQL and their support ticket count from MongoDB. Which tools do I call, in what order, and how do I combine the results?

**Expected answer (summary):**
Call `query_db` for PostgreSQL revenue data using standard SQL. Call `query_db` separately for MongoDB ticket count using a MongoDB aggregation pipeline. Then call `execute_python` to merge the two result sets in Python. Never attempt a cross-database join at the SQL level.

**Actual answer from LLM:**
Based on the document, here's the sequence for handling this cross-database query:

**Tools to call in order:**

1. **`query_db`** - Query PostgreSQL for customer revenue data
   - Use standard SQL (PostgreSQL 17.9) syntax
   - Connection: host=127.0.0.1, port=5432, user=oracleforge

2. **`query_db`** - Query MongoDB for support ticket count data
   - Use MongoDB aggregation pipeline JSON syntax (NOT SQL)
   - Format: `[{"$match": {...}}, {"$group": {...}}]`
   - Connection: mongodb://oracleforge:Oracle2026!@localhost:27017/?authSource=admin

3. **`execute_python`** - Merge the results from both databases
   - Fetch results from each database into Python variables
   - Perform the data merging/joining in Python code
   - Do NOT attempt cross-database joins at the SQL level

4. **`return_answer`** - Return the final merged result
   - Use this to terminate the agent loop with the complete answer

**Key principle:** The document emphasizes that when a query spans two databases, you must "route sub-queries to each database separately using `query_db`" and "merge results using `execute_python`" - never attempt cross-database joins at the SQL level.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer with correct tool order, proper database-specific syntax requirements, Python merging approach, and explicit prohibition of cross-database joins, plus adds helpful implementation details.

---

### Question 2 — PASS (95/100)

**Question:** I need to query a DuckDB dataset. What query dialect do I use and what functions are available that are not in standard PostgreSQL SQL?

**Expected answer (summary):**
Use analytical SQL with DuckDB extensions. DuckDB supports `UNNEST`, `LIST_AGG`, `STRUCT`, and columnar functions. Do not use PostgreSQL-specific syntax. The database file path is defined in the dataset's db_config.yaml.

**Actual answer from LLM:**
Based on the document, for querying a DuckDB dataset:

**Query dialect:** Analytical SQL with DuckDB extensions

**Tool to use:** `query_db`

**DuckDB-specific functions available (that are not in standard PostgreSQL SQL):**
- `UNNEST`
- `LIST_AGG` 
- `STRUCT`
- Columnar functions (specific functions not detailed in the document)

**Important notes:**
- DuckDB is efficient for aggregations over large datasets
- It's file-based with no server required
- Database file path is defined in db_config.yaml
- You should use DuckDB-native functions and NOT use PostgreSQL-specific syntax
- Do not attempt cross-database joins at the SQL level

**Grader reasoning:** The actual answer contains all key concepts from the expected answer plus additional relevant details without any contradictions.

---

### Question 3 — PASS (95/100)

**Question:** What is the purpose of the `return_answer` tool and when should I use it?

**Expected answer (summary):**
`return_answer` terminates the agent loop and records the final answer. Use it only when the answer is verified and complete. It is the last tool called in any successful agent run.

**Actual answer from LLM:**
Based on the document, the `return_answer` tool has the following purpose and usage:

**Purpose:** Terminate the agent loop and record the final answer

**When to use it:** When the answer is verified and complete

The document lists `return_answer` as one of the four agent tools available in every session, specifically for ending the workflow once you have determined the final, complete, and verified answer to the question or task at hand.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer (terminates agent loop, records final answer, use when verified and complete) with accurate information and good structure, only missing the explicit statement that it's the last tool called.

---

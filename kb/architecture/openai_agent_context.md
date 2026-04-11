# OpenAI in-house data agent — six-layer context architecture

## What this is

This document describes the six-layer context system from OpenAI's internal data agent, published January 2026. This agent serves 4,000+ employees across 600 petabytes and 70,000 datasets. The Oracle Forge agent implements minimum three of these six layers.

## The core problem this architecture solves

- Finding the right table is the hardest sub-problem — not query generation.
- Many tables look similar on the surface but differ critically in actual data content.
- Example: one table includes only logged-in users; another includes everyone. One captures only first-party traffic; another captures everything.
- Without layered context, the agent picks the wrong table and produces a wrong answer that looks correct.
- No SQL error fires. The answer simply uses the wrong data.
- Standard error handling does not catch this. No exception is raised. The wrong result is indistinguishable from a correct one at the system level.

**This is the same problem Oracle Forge faces on DataAgentBench:**

- DAB has multiple databases with similarly-named tables that have different semantics.
- DAB has inconsistently-formatted join keys across database systems. A customer ID is an integer in PostgreSQL and a "CUST-00123" string in MongoDB. This is a join key mismatch.
- DAB has domain-specific business terms not derivable from the schema. "active customer" means purchased in the last 90 days, not row existence. This cannot be inferred from the schema.
- The six-layer architecture gives the agent context to distinguish these categories before answering.

## The six layers in order

### Layer 1 — Schema metadata and historical queries

- Basic table structure: column names, data types, primary keys, foreign key relationships.
- Historical queries showing which tables are typically used together.
- Oracle Forge equivalent: `list_db` tool output.

### Layer 2 — Human-curated expert descriptions

- Domain experts write descriptions of key tables: what the table actually contains, known limitations, data quality caveats.
- Oracle Forge equivalent: `kb/domain/schemas.md` written by Intelligence Officers from `db_description.txt` and `db_description_with_hint.txt`.

### Layer 3 — Codex Enrichment (code-level table definitions)

- Codex Enrichment is Layer 3.
- It is a daily asynchronous process — not real-time, not triggered at query time.
- OpenAI runs it overnight as a background job.
- Codex crawls the codebase that generates each data table.
- It derives a deeper definition of each table from the pipeline code itself.
- From that code, Codex infers: upstream and downstream dependencies, ownership, granularity, join keys — facts that never appear in SQL schema metadata.
- Pipeline logic captures filtering assumptions invisible in schemas. Example: code reveals a table filters to only US users before aggregating — invisible in the SQL schema, visible in the pipeline code.
- Many tables look identical in their SQL schema but differ critically in actual data content. Codex Enrichment finds these differences by reading the code that generates the table.

### Layer 4 — Institutional knowledge

- The agent searches internal documents for product launch announcements, technical incident reports, and canonical metric definitions.
- Oracle Forge equivalent: `kb/domain/business_terms.md`.

### Layer 5 — Learning memory

- Layer 5 is the learning memory.
- The agent stores corrections and nuances discovered in previous conversations.
- It applies those corrections automatically to future requests.
- This solves the problem of repeated failures from the same mistake across sessions.
- Example correction stored: "The join between the customer table and the transaction table requires zero-padding the customer ID to 5 digits."
- **Measured impact:** a query that took over 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled.
- Oracle Forge equivalent: `kb/corrections/log.md` — structured log of `[query that failed] → [what was wrong] → [correct approach]`.
- The agent reads the last 10 entries at every session start — not all entries, only the last 10.

### Layer 6 — Runtime context (live schema inspection)

- When no prior information exists or existing data is outdated, the agent inspects the live data warehouse directly.
- Oracle Forge equivalent: `execute_python` + `query_db` fallback via `list_db`.

## The closed-loop self-correction pattern

- The agent evaluates its own intermediate results during execution — not only at the end.
- If an intermediate result looks wrong (zero rows from an expected join, a count too high, a metric contradicting a baseline) — the agent does not return the result.
- The agent investigates: checks join keys, filter conditions, whether the correct table was selected.
- The agent adjusts its approach and retries without surfacing the failure to the user.
- It carries the finding forward as a correction log entry so the same mistake does not recur in future sessions.

**This is not error handling:**

- Error handling reacts to exceptions raised by the system.
- Self-correction evaluates the quality of the agent's own reasoning even when no exception is raised.
- A wrong answer that looks correct will not trigger any system exception.
- Self-correction catches it by checking whether the result is plausible.
- Oracle Forge implements this in `self_corrector.py`.

## Three engineering lessons from OpenAI

**Lesson 1 — Tool consolidation matters:**

- Overlapping tools with redundant functionality confuse the agent.
- Restrict to one tool per database type with tight domain boundaries.
- Same principle as Claude Code's tool scoping philosophy.

**Lesson 2 — Less prescriptive prompting:**

- Rigid step-by-step instructions pushed the agent down wrong paths when the situation did not match the script.
- Higher-level guidance combined with model reasoning produces more robust results.

**Lesson 3 — Code reveals what metadata hides:**

- Pipeline logic contains filtering assumptions that never surface in table schemas.
- Crawling the codebase that generates tables provides more useful context than reading the tables themselves.
- Reading a table schema tells you column names. Reading the code that generates the table tells you what was filtered, transformed, and assumed.

## What this does NOT cover

Claude Code three-layer memory architecture is in claude_code_memory.md. Specific tool routing for DAB database types is in tool_scoping.md. Oracle Forge KB structure is in kb_v1_architecture.md.

---

Injection test: "What is Layer 5 in OpenAI's six-layer context architecture, and what is the Oracle Forge equivalent?"
Expected answer: Layer 5 is the learning memory — the agent stores corrections and nuances from previous conversations and applies them to future requests. Without memory a query took over 22 minutes; with memory it dropped to 1 minute 22 seconds. The Oracle Forge equivalent is kb/corrections/log.md — a running structured log of failed queries with what was wrong and the correct approach. The agent reads the last 10 entries at every session start.
Token count: ~430 tokens
Last verified: 2026-04-11

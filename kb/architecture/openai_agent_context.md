# OpenAI in-house data agent — six-layer context architecture

## What this is
This document describes the six-layer context system from OpenAI's internal data agent, published January 2026. This agent serves 4,000+ employees across 600 petabytes and 70,000 datasets. The Oracle Forge agent implements minimum three of these six layers. Study this document to understand why context layering exists and what each layer contributes.

## The core problem this architecture solves
Finding the right table is the hardest sub-problem — not query generation. Many tables look similar on the surface but differ critically: one table includes only logged-in users, another includes everyone; one captures only first-party traffic, another captures everything. Without layered context, the agent picks the wrong table and produces a wrong answer that looks correct. No SQL error fires. The answer simply uses the wrong data.

This is the same problem the Oracle Forge agent faces on DataAgentBench. DAB has multiple databases with similarly-named tables that have different semantics. DAB has inconsistently-formatted join keys across database systems — a customer ID is an integer in PostgreSQL and a "CUST-00123" string in MongoDB. DAB has domain-specific business terms that are not derivable from the schema alone — "active customer" means purchased in the last 90 days, not row existence. The six-layer architecture exists to give the agent the context to distinguish these three categories of problem before answering.

## The six layers in order

### Layer 1 — Schema metadata and historical queries
Basic table structure: column names, data types, primary keys, foreign key relationships. Historical queries that show which tables are typically used together. This is what `list_db` provides in the Oracle Forge agent. Load this layer after the question arrives and the relevant datasets are identified.

### Layer 2 — Human-curated expert descriptions
Domain experts write descriptions of key tables and dashboards: what the table actually contains, known limitations, data quality caveats. In the Oracle Forge context, this is `kb/domain/schemas.md` — written by Intelligence Officers based on reading `db_description.txt` and `db_description_with_hint.txt` for each DAB dataset.

### Layer 3 — Codex Enrichment (code-level table definitions)
Codex Enrichment is Layer 3. It is a daily asynchronous process — not real-time. OpenAI runs it overnight as a background job. Codex crawls the codebase that generates each data table and derives a deeper definition from the pipeline code itself. From that code, Codex infers each table's upstream and downstream dependencies, ownership, granularity, and join keys — facts that never appear in SQL schema metadata or column names. Pipeline logic also captures filtering assumptions and freshness guarantees invisible in schemas. Example: the code reveals that a table filters to only US users before aggregating — a fact invisible in the schema. Many tables look identical in their schema but differ critically in actual data content. Crawling the codebase that generates tables provides more useful context than reading the tables themselves.

### Layer 4 — Institutional knowledge
The agent searches internal documents for product launch announcements, technical incident reports, and canonical metric definitions. In the Oracle Forge context, this is `kb/domain/business_terms.md` — definitions of domain-specific terms not derivable from the schema alone.

### Layer 5 — Learning memory (self-correction loop)
The agent stores corrections and nuances discovered in previous conversations and applies them automatically to future requests. Example: "The join between the customer table and the transaction table requires zero-padding the customer ID to 5 digits." In the Oracle Forge context, this is `kb/corrections/log.md` — the running structured log of `[query that failed] → [what was wrong] → [correct approach]`. The agent reads the last 10 entries at every session start — not all entries, only the last 10. This layer reduces repeated failures from the same mistake.

Impact measured by OpenAI: a query that took 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled. Memory is non-negotiable.

### Layer 6 — Runtime context (live schema inspection)
When no prior information exists or existing data is outdated, the agent inspects the live data warehouse directly. This is the `execute_python` + `query_db` fallback: if the KB does not have information about a table's structure, run `list_db` to inspect it live.

## The closed-loop self-correction pattern

The agent evaluates its own intermediate results during execution — not only at the end. This evaluation happens mid-execution after every tool call that returns data. If an intermediate result looks wrong — zero rows from an expected join, a count that seems too high, a metric that contradicts a known baseline — the agent does not return the result. It investigates: checks the join keys, checks the filter conditions, checks whether the correct table was selected. Then it adjusts its approach and retries. It carries the finding forward as a correction log entry so the same mistake does not recur.

This is not error handling. Error handling reacts to exceptions raised by the system. Self-correction is different — it evaluates the quality of the agent's own reasoning even when no exception is raised. A wrong answer that looks correct will not trigger any system exception, but self-correction catches it by checking whether the result is plausible. The Oracle Forge agent implements this in `self_corrector.py`.

## Key engineering lessons from OpenAI

Tool consolidation matters: overlapping tools confuse the agent. Restrict to one tool per database type with tight domain boundaries — the same principle as Claude Code's tool scoping philosophy.

Less prescriptive prompting: rigid step-by-step instructions pushed the agent down wrong paths when the situation did not match the script. Higher-level guidance plus model reasoning produces more robust results.

Code reveals what metadata hides: pipeline logic contains assumptions that never surface in table schemas. Crawling the codebase that generates tables provides more useful context than reading the tables themselves — reading the table schema tells you column names; reading the code that generates the table tells you what was filtered, transformed, and assumed.

## What this does NOT cover
The Claude Code three-layer memory architecture is in claude_code_memory.md. The specific tool routing for DAB database types is in tool_scoping.md. The Oracle Forge KB structure is in kb_v1_architecture.md.

---
Injection test: "What is Layer 5 in OpenAI's six-layer context architecture, and what is the Oracle Forge equivalent?"
Expected answer: Layer 5 is the learning memory — the agent stores corrections and nuances from previous conversations and applies them to future requests. Without memory, a query that took 22 minutes dropped to 1 minute 22 seconds with it. The Oracle Forge equivalent is kb/corrections/log.md — a running structured log of failed queries with what was wrong and the correct approach. The agent reads the last 10 entries at every session start.
Token count: ~390 tokens
Last verified: 2026-04-11
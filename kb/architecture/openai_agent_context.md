# OpenAI in-house data agent — six-layer context architecture

## What this is
This document describes the six-layer context system from OpenAI's internal data agent, published January 2026. This agent serves 4,000+ employees across 600 petabytes and 70,000 datasets. The Oracle Forge agent implements minimum three of these six layers. Study this document to understand why context layering exists and what each layer contributes.

## The core problem this architecture solves
Finding the right table across 70,000 datasets and 600 petabytes is the hardest sub-problem — not query generation. Many tables look similar on the surface but differ critically: one table includes only logged-in users, another includes everyone; one captures only first-party traffic, another captures everything. Without layered context, the agent picks the wrong table and produces a wrong answer that looks correct. This is the same problem the Oracle Forge agent faces on DAB: multiple databases, similar-looking schemas, different semantics.

## The six layers in order

### Layer 1 — Schema metadata and historical queries
Basic table structure: column names, data types, primary keys, foreign key relationships. Historical queries that show which tables are typically used together for which types of analysis. This is what `list_db` provides in the Oracle Forge agent. Load this layer after the question arrives and the relevant datasets are identified.

### Layer 2 — Human-curated expert descriptions
Domain experts write descriptions of key tables and dashboards: what the table actually contains (not just what its schema says), known limitations, data quality caveats, which columns are reliable. In the Oracle Forge context, this is `kb/domain/schemas.md` — the Intelligence Officers write these descriptions based on reading `db_description.txt` and `db_description_with_hint.txt` for each DAB dataset.

### Layer 3 — Codex Enrichment (code-level table definitions)
OpenAI crawls the codebase daily using Codex to derive each table's meaning from the pipeline code that generates it. Pipeline logic captures assumptions, freshness guarantees, and business intent that never appear in SQL or metadata. Example: the code reveals that a table filters to only US users before aggregating — a fact invisible in the schema. In the Oracle Forge context, this corresponds to reading the DAB query patterns and understanding what the queries assume about the data.

### Layer 4 — Institutional knowledge
The agent searches Slack messages, Google Docs, and Notion documents for product launch announcements, technical incident reports, and canonical metric definitions. Example: "active user" is defined differently in different parts of the organization — the institutional knowledge layer resolves which definition applies to the current question. In the Oracle Forge context, this is `kb/domain/business_terms.md` — definitions of domain-specific terms that are not derivable from the schema alone.

### Layer 5 — Learning memory (self-correction loop)
The agent stores corrections and nuances discovered in previous conversations and applies them to future requests. Example: "The join between the customer table and the transaction table requires zero-padding the customer ID to 5 digits." This is stored as a correction and loaded at the start of every future session. In the Oracle Forge context, this is `kb/corrections/log.md` — the running structured log of `[query that failed] → [what was wrong] → [correct approach]`. The agent reads the last 10 entries at session start. This layer reduces repeated failures from the same mistake.

Impact measured by OpenAI: a query that took 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled. Memory is non-negotiable.

### Layer 6 — Runtime context (live schema inspection)
When no prior information exists or existing data is outdated, the agent inspects the live data warehouse directly. This is the `execute_python` + `query_db` fallback in the Oracle Forge agent: if the KB does not have information about a table's structure, run `list_db` to inspect it live.

## The closed-loop self-correction pattern

If an intermediate result looks wrong — zero rows from an expected join, a count that seems too high, a metric that contradicts a known baseline — the agent does not return the result. It investigates: checks the join keys, checks the filter conditions, checks whether the correct table was selected. Then it adjusts its approach and retries. It carries the finding forward as a correction log entry so the same mistake does not recur.

This is not error handling. It is the agent evaluating its own reasoning mid-execution. The Oracle Forge agent implements this in `self_corrector.py` — detect execution failure, diagnose which of the four failure categories applies (wrong tool, wrong join key, unstructured text not extracted, domain term misunderstood), then retry with the correct approach.

## Key engineering lessons from OpenAI

Tool consolidation matters: overlapping tools confuse the agent. Restrict to one tool per database type with tight domain boundaries — the same principle as Claude Code's tool scoping philosophy.

Less prescriptive prompting: rigid step-by-step instructions pushed the agent down wrong paths when the situation did not match the script. Higher-level guidance plus model reasoning produces more robust results.

Code reveals what metadata hides: pipeline logic contains assumptions that never surface in table schemas. Reading the code that generates a table tells you more than reading the table's schema.

## What this does NOT cover
The Claude Code three-layer memory architecture is in claude_code_memory.md. The specific tool routing for DAB database types is in tool_scoping.md. The Oracle Forge KB structure is in kb_v1_architecture.md.

---
Injection test: "What is Layer 5 in OpenAI's six-layer context architecture, and what is the Oracle Forge equivalent?"
Expected answer: Layer 5 is the learning memory — the agent stores corrections and nuances from previous conversations and applies them to future requests. Without memory, a query that took 22 minutes dropped to 1 minute 22 seconds with it. The Oracle Forge equivalent is kb/corrections/log.md — a running structured log of failed queries with what was wrong and the correct approach. The agent reads the last 10 entries at every session start.
Token count: ~380 tokens
Last verified: 2026-04-11
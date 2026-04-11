# OpenAI Data Agent — Codex-Powered Table Enrichment

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: OpenAI Engineering Blog, January 29 2026_

### The Problem

Raw schema tells you: table `users`, column `status`, type `integer`.

It does **not** tell you:

- `status = 1` means "active"
- `status = 2` means "suspended"
- `status = 3` means "deleted" (but records remain for audit)

Without enrichment, the agent produces **syntactically correct but semantically
wrong** queries.

### The OpenAI Solution

A specialized Codex model (not the main agent LLM) runs daily as an async process:

1. **Scan** table and column names
2. **Generate** plausible business descriptions from pipeline code
3. **Present** descriptions to human data stewards for verification
4. **Store** verified descriptions in the enrichment layer

### The Closed-Loop Self-Correction Pattern

1. Agent runs query with current enrichment
2. User corrects output ("That's not what churn means here")
3. Correction flows to enrichment layer (not just session memory)
4. Next query uses corrected enrichment

### Oracle Forge Equivalent

We cannot run a daily Codex async pipeline in two weeks. Our equivalent:

- `schema_introspector` utility runs at **agent startup** (not daily async)
- Human-verified column semantics written manually into `kb/domain/schema_descriptions.md`
- Corrections flow to KB v3 and are injected on the next session

### Key Insight

**Table enrichment is the difference between a demo agent and a production agent.**
A demo agent assumes schema is self-documenting. A production agent knows that
`status = 2` means suspended and filters accordingly.

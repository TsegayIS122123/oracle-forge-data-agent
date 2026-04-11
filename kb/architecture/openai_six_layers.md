# OpenAI Data Agent — Six-Layer Context Architecture

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: OpenAI Engineering Blog, January 29 2026_

_Scale: 600+ PB, 70,000 datasets, 3,500+ internal users_

### The Core Problem

Finding the right table across 70,000 datasets is the hardest sub-problem.
Many tables look similar on the surface but differ critically — one includes
only logged-in users, another includes logged-out users too. Context engineering
is the bottleneck, not query generation.

### The Six Layers (cumulative — each builds on the previous)

| Layer | Name                        | What It Provides                                                                                                                         |
| ----- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | **Raw Schema**              | Table names, column names, data types via `INFORMATION_SCHEMA`. No business meaning — only structure                                     |
| 2     | **Table Relationships**     | Foreign key relationships, join paths inferred from schema constraints and query history                                                 |
| 3     | **Column Semantics**        | What each column means in business terms. Example: `status_code = 3` means "active customer." Source: data dictionary, human annotation  |
| 4     | **Query Patterns**          | Common joins, aggregations, filters that work. Example: "Always filter `deleted_at IS NULL` before counting users." Source: log analysis |
| 5     | **Institutional Knowledge** | Domain-specific definitions not in schema. Example: "Churn = no purchase in 90 days." Source: business documentation                     |
| 6     | **User Preferences**        | Individual preferred aggregations, date ranges, output formats. Source: session history                                                  |

### Application to Oracle Forge

| OpenAI Layer        | DAB Agent Implementation                     |
| ------------------- | -------------------------------------------- |
| 1: Raw Schema       | MCP Toolbox introspection at startup         |
| 2: Relationships    | Foreign keys from `information_schema`       |
| 3: Column Semantics | `kb/domain/schema_descriptions.md`           |
| 4: Query Patterns   | `kb/domain/query_patterns.md`                |
| 5: Institutional    | `kb/domain/domain_terms.md`                  |
| 6: User Preferences | Future iteration — out of scope for Week 8-9 |

**Minimum viable for DAB:** Layers 1, 3, and 5 must demonstrably work.
Layer 3 (Column Semantics) is the hardest — document what `user_id` means
in PostgreSQL vs. `cust_id` in MongoDB **before** the agent runs its first query.

### Self-Correction Loop

- If intermediate result looks wrong (zero rows, unexpected nulls), agent
  diagnoses, adjusts, retries
- Does NOT surface the error to the user
- Carries learnings forward between steps
- Result: analysis time dropped from 22 minutes to 90 seconds with memory enabled

### Key Insight

**Layer 3 (Column Semantics) is the hardest sub-problem.** OpenAI explicitly calls
out table enrichment as the bottleneck. For DAB, this means documenting what
`user_id` means in PostgreSQL vs. `cust_id` in MongoDB before the agent runs
its first query.

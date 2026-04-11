# The Oracle Forge Architecture — System Overview

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

```
USER INPUT (Natural Language Question)
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│               LAYER 1: CONTEXT COMPILER (The Driver)                  │
│   Responsibility: Assemble the exact context window for the LLM.      │
│                                                                       │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌────────────────┐  │
│  │  KB v1/v2 (Static)  │ │ KB v3 (Corrections) │ │Schema Introsp. │  │
│  │  - Domain Terms     │ │ - "Last time we     │ │- MCP Toolbox   │  │
│  │  - Join Key Glossary│ │   failed on ID fmt" │ │  Routing Info  │  │
│  └─────────────────────┘ └─────────────────────┘ └────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│               LAYER 2: REASONING & ROUTING (LLM)                      │
│   Prompt: "You have access to PG, Mongo, SQLite. Use the glossary     │
│            to resolve 'churn'. Check corrections log before executing."│
└───────────────────────────────────────────────────────────────────────┘
        │
        │  (Agent outputs: Plan to query PG users + Mongo support_notes)
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│           LAYER 3: SELF-CORRECTING EXECUTION LOOP                     │
│                   (The Sentinel / Sandbox)                            │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │  PostgreSQL  │  │   MongoDB    │  │  Unstructured Extraction  │    │
│  │  (Users)     │─▶│  (Tickets)   │  │  (Week 3 pipeline)        │    │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘    │
│                           │                                           │
│                           ▼                                           │
│                  ┌─────────────────────┐                              │
│                  │   JOIN RESOLVER     │ ◀── FAILS? (ID mismatch)     │
│                  │  ──RETRY──▶ Write to KB v3                         │
│                  └─────────────────────┘                              │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      EVALUATION HARNESS                               │
│  - Traces every tool call (PostgreSQL tool, Mongo tool, Python exec)  │
│  - Compares output to DAB Expected Result                             │
│  - Updates Score Log                                                  │
└───────────────────────────────────────────────────────────────────────┘
        │
        ▼
FINAL VERIFIABLE OUTPUT + TRACE
```

**How the three KB documents map to this architecture:**

- **KB v1** (this document) feeds Layer 1 — the architectural patterns that govern
  how the context compiler, routing logic, and execution loop are designed
- **KB v2** feeds Layer 1 — the domain knowledge (schema descriptions, join key
  glossary, domain terms) injected before every query
- **KB v3** feeds Layer 1 — the corrections log injected as "do not repeat these
  mistakes" at the start of every session

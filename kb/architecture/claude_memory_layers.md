# Claude Code — Three-Layer Memory Architecture

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: Claude Code npm leak, March 31 2026 — 512,000 lines TypeScript_

### Core Insight

Claude Code solves "context entropy" — the tendency for long agent sessions to become
confused — through a three-layer memory architecture that treats memory as an
**external system**, not part of the context window.

### Layer 1 — MEMORY.md (Index Layer)

- **Location:** Project root
- **Purpose:** Entry point for context loading — lightweight pointer index
  (~150 chars per entry)
- **Content:** High-level project structure, key conventions, pointers to topic files
- **When loaded:** At every session start — perpetually in context
- **Never stores actual information — only pointers**
- **Read-before-write discipline:** agent reads current MEMORY.md before any
  update to prevent overwrite
- **Self-healing:** if the agent learns a prior assumption was wrong, it rewrites
  the relevant memory file so the correction persists across sessions

### Layer 2 — Topic Files (Detailed Knowledge)

- **Location:** `.claude/memory/` directory
- **Purpose:** Deep knowledge on specific domains
- **Content:** Detailed instructions for testing, deployment, database schema, etc.
- **When loaded:** On-demand when agent encounters relevant task
- **Trigger:** Keyword matching or explicit agent request
- Only files **relevant to the current task** are loaded — not a full dump

### Layer 3 — Session Transcripts (Interaction Memory)

- **Location:** `.claude/sessions/`
- **Purpose:** Searchable record of past interactions
- **Content:** Full conversation history, tool calls, outputs, user corrections
- **When loaded:** Agent searches transcripts when uncertain or user references
  past work
- **Search method:** Embedding-based semantic search

### Application to Oracle Forge

| Claude Code Pattern | DAB Agent Implementation                                           |
| ------------------- | ------------------------------------------------------------------ |
| MEMORY.md index     | AGENT.md — DB connection summary and KB pointers                   |
| Topic files         | `kb/domain/` directory with schema details per dataset             |
| Session transcripts | `kb/corrections/kb_v3_corrections.md` with structured failure logs |

### Key Insight

The three layers prevent context window bloat. The agent navigates from
index → topic → transcript only when needed. Apply the same principle:
do not inject all KB documents into every query — inject only what that
query needs.

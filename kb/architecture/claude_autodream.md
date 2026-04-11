# Claude Code — autoDream Memory Consolidation

_The Oracle Forge | Intelligence Officers | April 2026_
s
_Status: v1.1 | Team Verified_

---

_Source: Claude Code npm leak, March 31 2026_

### The Pattern

autoDream is an asynchronous background process that:

1. **Orient** — Read MEMORY.md to understand current state
2. **Gather** — Find new signals from daily logs and session transcripts
3. **Consolidate** — Merge disparate observations, remove contradictions,
   convert vague insights to concrete facts
4. **Prune** — Keep context efficient by removing stale or redundant entries

### Consolidation Triggers (from source code)

- User corrects same pattern 3+ times → Write to MEMORY.md
- Agent successfully uses a pattern 5+ times → Promote to topic file
- Topic file grows beyond 500 words → Split into subtopics

### The "Dream" Metaphor

The system processes memory **offline**, not during active sessions. This prevents
the consolidation work from consuming the agent's context window or slowing
response time.

### Application to Oracle Forge

| autoDream Function | DAB Agent Implementation                                   |
| ------------------ | ---------------------------------------------------------- |
| Pattern detection  | Manual review of `kb/corrections/` after each test run     |
| Consolidation      | IOs update `kb/domain/` based on observed failure patterns |
| Pruning            | Weekly CHANGELOG.md review to remove obsolete entries      |

### Key Insight

The value is not the automation — it is the **structured format**. Every correction
follows: `[Query] → [What failed] → [Correct approach]`. This format makes the
knowledge injectable into future LLM contexts. KB v3 is a manual autoDream.

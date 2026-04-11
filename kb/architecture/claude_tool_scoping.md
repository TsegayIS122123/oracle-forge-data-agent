# Claude Code — Tool Scoping Philosophy

_The Oracle Forge | Intelligence Officers | April 2026_

_Status: v1.1 | Team Verified_

---

_Source: Claude Code npm leak, March 31 2026_

### The Pattern

Claude Code exposes 40+ tools to the agent, but each tool has:

- **Tight domain boundaries** — one tool does one thing well
- **Explicit preconditions** — what must be true before calling
- **Clear error semantics** — what failure means and how to recover

### Tool Categories

1. **File System:** `read_file`, `write_file`, `list_directory`, `search_content`
2. **Code Execution:** `run_terminal`, `run_python`, `run_tests`
3. **Git:** `git_status`, `git_diff`, `git_commit`, `git_branch`
4. **External:** `web_search`, `web_fetch`, `api_call`

### The "Tool First" Design Rule

Tools are designed **before** the agent prompt. The prompt references tools by
name and purpose. The agent never generates raw shell commands — it selects tools
from the manifest.

### Application to Oracle Forge

| Claude Code Tool | DAB Agent Equivalent                         |
| ---------------- | -------------------------------------------- |
| `run_terminal`   | MCP Toolbox PostgreSQL executor              |
| `search_content` | Schema introspection via MCP                 |
| `git_diff`       | Query trace comparison in evaluation harness |

### Required MCP Tools for DAB

1. `query_postgres_[dataset]` — one tool per PostgreSQL database
2. `query_mongo_[collection]` — one tool per MongoDB collection
3. `extract_structured_text` — unstructured field parser (Week 3 module)
4. `resolve_join_key` — format normalizer for cross-DB joins

### Key Insight

**Do not give the agent raw SQL execution. Give it named tools.** This enables:

- Query tracing (evaluation harness requirement)
- Automatic dialect translation (PostgreSQL vs. SQLite vs. DuckDB)
- Failure recovery (tool returns structured error, agent can retry)

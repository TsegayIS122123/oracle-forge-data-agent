# Claude Code three-layer memory architecture

## What this is
This document describes the memory system extracted from the Claude Code source snapshot (March 2026 leak, ~512,000 lines of TypeScript). This architecture is the direct model for how the Oracle Forge agent manages its own context across sessions. Apply these patterns when making decisions about what to load, when to load it, and what to consolidate.

## The three memory layers

### Layer 1 — MEMORY.md index (~200 tokens, always loaded)
MEMORY.md is a small index file — not a knowledge document itself. It lists every other KB document by name with a one-sentence description. The agent reads this file first at session start to know what knowledge is available, then uses it to decide what to load next. It is never more than ~200 tokens. Growing it beyond this defeats its purpose.

Source in codebase: `src/memdir/` handles the memory directory. The MEMORY.md file is the index of this directory. It functions like a table of contents — pointing to topic files, not containing content itself.

### Layer 2 — Topic files (~300-400 tokens each, loaded on demand)
Topic files contain the actual knowledge for a specific subject — tool scoping, schema details, business terms, join key glossaries. They are loaded only when the MEMORY.md index indicates they are relevant to the current question. A session that asks about PostgreSQL schemas loads the schema topic file. A session that asks about MongoDB aggregation loads tool_scoping.md. A session about stock data loads the stockmarket schema section. Never load all topic files upfront.

Source in codebase: `src/services/extractMemories/` auto-extracts memories from conversations and writes them back to topic files. `src/services/teamMemorySync/` synchronizes topic files across team members.

### Layer 3 — Session transcripts (searched, never pre-loaded)
Session transcripts are logs of past agent runs — which queries were asked, what tools were called, what results came back, what the final answer was. They are never pre-loaded into context. The agent searches them when a new question closely resembles a past one (e.g., "This looks like the bookreview query 3 pattern — retrieve the transcript"). Searching is cheap; pre-loading is expensive.

Source in codebase: `src/commands/resume` implements session restoration from transcript. The query pipeline in `src/QueryEngine.ts` (~46K lines) manages context window budgets that enforce this never-pre-load discipline.

## The autoDream consolidation pattern

Source in codebase: `src/tasks/DreamTask/` and `src/services/autoDream/`.

After a session ends, autoDream runs as a background process. It reviews what was learned during the session — corrections made, successful query patterns, new business term definitions discovered — and consolidates them back into the relevant topic files. Old, superseded information is removed. The topic file after consolidation is smaller and more precise than before the session. This is the mechanism that prevents the KB from growing into noise.

Apply this pattern to the Oracle Forge KB: after every batch of agent runs, review the corrections log and consolidate verified fixes back into domain documents. Remove entries from the corrections log that have been absorbed into the main topic files.

## Tool scoping philosophy (40+ tools, tight domain boundaries)

Source in codebase: `src/tools/` contains ~40 tool implementations. `src/Tool.ts` (~29K lines) defines the base type with input schema (Zod validation), permission model, and execution logic.

Claude Code's tool scoping principle: every tool has a single, tight responsibility with a named domain boundary. A tool that does one thing precisely is more reliable than a tool that tries to do three things loosely. The agent knows exactly which tool failed and why — because each tool does exactly one thing. This is directly why the Oracle Forge agent uses separate tools per database type rather than a single "query database" tool that switches internally.

The permission model per tool (not per session): each tool declares what user approvals it requires, what it is safe to do without approval, and whether it is concurrency-safe. The Oracle Forge DAB tools are all read-only — `checkPermissions()` auto-approves all database queries.

## Worktree sub-agent spawn modes

Source in codebase: `src/tools/EnterWorktreeTool.ts`, `src/tools/ExitWorktreeTool.ts`, `src/coordinator/`.

Claude Code spawns sub-agents into isolated git worktrees for parallel experiments. Each worktree is an isolated copy of the repository state — experiments in one worktree cannot interfere with another. The Coordinator (`src/coordinator/coordinatorMode.ts`) orchestrates which sub-agents run in which worktrees and merges their outputs.

For the Oracle Forge agent: the evaluation harness uses this pattern — multiple trial runs of the same query run in isolation and their results are aggregated by the harness, not interfered with by each other.

## What this does NOT cover
The OpenAI six-layer context design is in openai_agent_context.md. The Oracle Forge KB structure rules are in kb_v1_architecture.md. Database tool routing specifics are in tool_scoping.md.

---
Injection test: "What is the purpose of MEMORY.md in Claude Code's memory system, and how does autoDream relate to it?"
Expected answer: MEMORY.md is a small index file (~200 tokens) that lists all topic files and their one-sentence descriptions. The agent reads it first to know what knowledge exists, then loads only the relevant topic files on demand. autoDream is a background process that runs after sessions end — it consolidates learnings from the session back into topic files and removes outdated information, keeping topic files minimal and precise.
Token count: ~390 tokens
Last verified: 2026-04-11
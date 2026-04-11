# Architecture Knowledge Base — Index

## What this is
This is the index of the Oracle Forge architecture knowledge base. Load this document first at every session start. It tells the agent what architecture documents exist and what each one contains. Use it to decide which documents to load next based on the question being asked.

## Document registry

### tool_scoping.md
What it contains: Which MCP tool to call for which database type. The exact mapping from database engine (PostgreSQL, MongoDB, SQLite, DuckDB) to the tool name and query dialect. Load this before every query — it is mandatory.
Token budget: ~300 tokens. Load: always, first.

### claude_code_memory.md
What it contains: Claude Code's three-layer memory architecture extracted from the March 2026 source leak. How the MEMORY.md index works, how topic files are loaded on demand, how session transcripts are searched but never pre-loaded, and the autoDream consolidation pattern.
Token budget: ~380 tokens. Load: when the agent needs to understand its own memory architecture or when implementing context layer decisions.

### openai_agent_context.md
What it contains: OpenAI's six-layer context architecture for their internal data agent (January 2026). The six layers in order, what Codex Enrichment is, how the self-learning memory loop works, and the closed-loop self-correction pattern.
Token budget: ~360 tokens. Load: when the agent needs to understand context layering strategy or how to handle table ambiguity.

### kb_v1_architecture.md
What it contains: How the Oracle Forge KB itself is structured. The four subdirectories (architecture, domain, evaluation, corrections), the Karpathy method discipline, the injection test protocol, and the token budget rules.
Token budget: ~300 tokens. Load: when the agent needs to understand its own knowledge base structure.

## Context loading order — follow exactly

```
1. Load kb/architecture/tool_scoping.md          [MANDATORY ~300 tok]
2. Load kb/corrections/log.md last 10 entries    [MANDATORY ~400 tok]
   → If missing: log "corrections log not yet created", continue
3. Load kb/architecture/MEMORY.md (this file)   [MANDATORY ~200 tok]
4. Receive the question
5. Identify which dataset(s) are involved
6. Load kb/domain/schemas.md for those datasets  [~400 tok per dataset]
7. If question uses ambiguous business language:
   load kb/domain/business_terms.md              [OPTIONAL ~300 tok]
8. Answer the question
```

Token budget rule — mandatory vs post-question:
- Steps 1–3 are the mandatory pre-load: ~900 tokens total. These load BEFORE the question arrives.
- Steps 5–8 load AFTER the question arrives and are NOT part of the ~900 mandatory budget.
- The ~700 optional budget covers post-question loads (schema + business_terms).
- Total maximum across a full session: ~1,600 tokens of KB context.
- Do not count schema loads in the mandatory pre-load total. They are question-specific and post-question.

Total pre-load budget: ~900 tokens mandatory (steps 1–3 only) + ~700 optional post-question maximum.

## What this does NOT cover
Domain schemas, join key formats, and unstructured field inventories are in kb/domain/. Agent failure corrections are in kb/corrections/. DAB benchmark scoring and evaluation methodology are in kb/evaluation/.

---
Token count: ~220 tokens
Last verified: 2026-04-11
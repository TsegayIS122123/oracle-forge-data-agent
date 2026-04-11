# Architecture Knowledge Base — Index

## What this is
This is the index of the Oracle Forge architecture knowledge base. Load this document first at every session start. It tells the agent what architecture documents exist and what each one contains. Use it to decide which documents to load next based on the question being asked.

## Document registry

### tool_scoping.md
What it contains: The exact database-to-tool mapping for all four DAB engine types — PostgreSQL, MongoDB, SQLite, and DuckDB — and which MCP tool to call for each engine and which query dialect to use. The tool scoping philosophy that each tool has a single tight responsibility — a tool that does one thing precisely is more reliable than a tool doing multiple things loosely — which is why the agent uses separate database tools instead of one general query tool. tool_scoping.md is mandatory and is already loaded as step 1 of every session — it is always in context when any question arrives.
Token budget: ~300 tokens. Load: always first. Already in context from session start.

### claude_code_memory.md
What it contains: Claude Code's three-layer memory architecture extracted from the March 2026 source leak. How the MEMORY.md index works, how topic files are loaded on demand, how session transcripts are searched but never pre-loaded, and the autoDream consolidation pattern.
Token budget: ~380 tokens. Load: on demand, when the agent needs to understand its own memory architecture or when implementing context layer decisions.

### openai_agent_context.md
What it contains: OpenAI's six-layer context architecture for their internal data agent (January 2026). The six layers in order, what Codex Enrichment is, how the self-learning memory loop works, and the closed-loop self-correction pattern.
Token budget: ~360 tokens. Load: on demand, when the agent needs to understand context layering strategy or how to handle table ambiguity.

### kb_v1_architecture.md
What it contains: How the Oracle Forge KB itself is structured. The four subdirectories (architecture, domain, evaluation, corrections), the Karpathy method discipline, the injection test protocol, and the token budget rules.
Token budget: ~300 tokens. Load: on demand, when the agent needs to understand its own knowledge base structure.

### kb/domain/business_terms.md
What it contains: Definitions of domain-specific terms not derivable from schema alone — what "churn" means, what "active customer" means, fiscal year boundaries, and status code meanings. This document is optional not mandatory. It is step 7 in the context loading order, triggered by detected ambiguity in the question — load it when and only when the question uses ambiguous business language that is not resolvable from the schema.
Token budget: ~300 tokens. Load: optional, post-question, step 7 only, triggered by detected ambiguity.

## Context loading order — follow exactly

```
Step 1: Load kb/architecture/tool_scoping.md     [MANDATORY ~300 tok — before question]
Step 2: Load kb/corrections/log.md last 10 entries [MANDATORY ~400 tok — before question]
         → If missing: log "corrections log not yet created", continue
Step 3: Load kb/architecture/MEMORY.md            [MANDATORY ~200 tok — before question]
Step 4: Receive the question
Step 5: Identify which dataset(s) are involved
Step 6: Load kb/domain/schemas.md for those datasets [~400 tok per dataset — post-question]
Step 7: If question uses ambiguous business language:
         load kb/domain/business_terms.md          [OPTIONAL ~300 tok — post-question]
Step 8: Answer the question
```

## Token budget — mandatory vs post-question

Mandatory pre-load (steps 1–3 only, load BEFORE the question arrives):
- Step 1: tool_scoping.md = ~300 tokens
- Step 2: corrections/log.md last 10 entries = ~400 tokens
- Step 3: MEMORY.md = ~200 tokens
- Mandatory pre-load total = ~900 tokens

Post-question budget (steps 5–7, load AFTER the question arrives):
- schemas.md per dataset section = ~400 tokens
- business_terms.md = ~300 tokens (optional)
- Post-question maximum = ~700 tokens

Total maximum across a full session = ~1,600 tokens of KB context.

Do not count schema loads in the mandatory pre-load total. Schema loads are question-specific and post-question. The breakdown of the 900-token mandatory budget is: tool_scoping.md 300 plus corrections log 400 plus MEMORY.md 200.

## What this does NOT cover
Domain schemas, join key formats, and unstructured field inventories are in kb/domain/. Agent failure corrections are in kb/corrections/. DAB benchmark scoring and evaluation methodology are in kb/evaluation/.

---
Token count: ~270 tokens
Last verified: 2026-04-11
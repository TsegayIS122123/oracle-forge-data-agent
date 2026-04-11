# Oracle Forge KB structure and discipline

## What this is
This document describes how the Oracle Forge Knowledge Base is organized, the rules that govern it, and the Karpathy method that keeps it from becoming noise. Load this document when the agent needs to understand its own knowledge base structure or when making decisions about what to add, remove, or update.

## The four KB subdirectories

### kb/architecture/
Contains documents about how the agent itself works: the memory architecture, tool scoping rules, context loading order, and this structural overview. Documents here are written for the agent about the agent. They change when the agent architecture changes. They do not change when DAB datasets change.

Files: MEMORY.md, tool_scoping.md, claude_code_memory.md, openai_agent_context.md, kb_v1_architecture.md (this file).

### kb/domain/
Contains documents about the data the agent works with: schema descriptions per DAB dataset, join key formats across database systems, unstructured field inventory, and business term definitions. Documents here change when datasets are loaded, when new failure patterns reveal schema misunderstandings, or when domain terms are corrected.

Files: schemas.md, join_key_glossary.md, unstructured_fields.md, business_terms.md.

### kb/evaluation/
Contains documents about how the agent is scored and what the benchmark requires: DAB query format, pass@1 scoring method, submission requirements, the four DAB failure categories, and what each failure category looks like in agent behavior.

Files: dab_overview.md, failure_taxonomy.md.

### kb/corrections/
`kb/corrections/log.md` is the self-learning loop. It is the running structured log of agent failures written by Drivers after every observed agent failure. The agent reads the last 10 entries at session start. Intelligence Officers prune outdated entries when newer ones supersede them.

Files: log.md

## The Karpathy method — minimum content, maximum precision

The Karpathy discipline is removal, not accumulation. Every document must be minimal and precise. Every document must pass an injection test before committing — this is not optional. A document that has not been injection-tested must not be loaded by the agent under any circumstances. Standard documentation practice grows over time by adding more content. The Karpathy method does the opposite: it shrinks documents by removing what is not proven to work. The Karpathy method requires removing everything the LLM already knows from pretraining. Only include content specific to DAB, these databases, and this agent — nothing general. A KB that grows without being tested becomes noise that degrades the agent. The test for every sentence is: if the agent read only this sentence with no other context, could it take the correct action? If no — rewrite it or cut it.

## Injection test protocol

```
Step 1: Copy the full text of the document.
Step 2: Open a completely fresh LLM session (no other context, no system prompt).
Step 3: Paste the document as the only content the LLM has seen.
Step 4: Ask the test question written at the bottom of the document.
Step 5: Grade: correct answer = PASS. Wrong or incomplete = FAIL.
Step 6: Write result to kb/architecture/injection_tests/[document_name]_test.md.
```

A document without a test result in its test file has not been validated and must not be loaded by the agent.

## Why MEMORY.md has the smallest token budget

MEMORY.md is capped at ~200 tokens because it is a pointer, not a topic document. Its only job is to list what other documents exist and what each one contains in one sentence. It is loaded at every session start before the question arrives — which means every token it consumes comes directly out of the mandatory pre-load budget before any question-specific loading has begun. If MEMORY.md grows beyond ~200 tokens it starts functioning as a topic document masquerading as an index: it wastes mandatory context budget on information that belongs in a topic file, and it defeats its own purpose by becoming something the agent needs to read carefully rather than scan quickly to decide what to load next. Keep it small on purpose. Any content that belongs in a topic file must be moved to that file, not added to MEMORY.md.

## Token budget summary

| Document | Budget | Load when |
|---|---|---|
| MEMORY.md | ~200 tok | Always first — mandatory |
| tool_scoping.md | ~300 tok | Always second — mandatory |
| corrections/log.md | ~400 tok (last 10 entries) | Always third — mandatory |
| claude_code_memory.md | ~380 tok | On demand |
| openai_agent_context.md | ~360 tok | On demand |
| kb_v1_architecture.md | ~300 tok | On demand |
| schemas.md (per dataset section) | ~400 tok | After question received |
| business_terms.md | ~300 tok | If ambiguous language detected |

Total mandatory pre-load: ~900 tokens (MEMORY.md 200 + tool_scoping.md 300 + corrections/log.md 400). Total optional post-question maximum: ~700 tokens.

## What this does NOT cover
The specific database tool assignments are in tool_scoping.md. Domain schemas and join keys are in kb/domain/. The agent failure corrections log is in kb/corrections/.

---
Injection test: "What are the four KB subdirectories in the Oracle Forge project and what does each one contain?"
Expected answer: kb/architecture/ contains documents about how the agent works (memory system, tool scoping, context loading). kb/domain/ contains documents about the data (schemas, join keys, business terms). kb/evaluation/ contains documents about scoring and the benchmark. kb/corrections/ contains the running log of agent failures and their fixes, read at every session start.
Token count: ~320 tokens
Last verified: 2026-04-11
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
Contains the running structured log of agent failures. This is the self-learning loop. The agent reads the last 10 entries at session start. Drivers write entries after every observed failure. Intelligence Officers prune outdated entries when newer ones supersede them.

Files: log.md

## The Karpathy method — minimum content, maximum precision

The discipline is removal, not accumulation. Every document must pass an injection test: paste it into a fresh LLM session with only that document as context, ask a question it should answer, and grade the result. Documents that fail the injection test are revised or removed — never kept.

A KB that grows without being tested becomes noise that degrades the agent. The goal is that an agent that loads only the relevant KB documents should be able to answer the question correctly — not an agent that loads everything.

Rules:
1. Every document has a stated token budget. Do not exceed it.
2. Remove everything the LLM already knows from pretraining. Only include what is specific to DAB, these databases, this agent.
3. Every document has a CHANGELOG.md tracking what changed, when, and why.
4. Every document has a corresponding injection test file in injection_tests/ documenting the test question, expected answer, and PASS/FAIL result.
5. Documents that have not been injection-tested have not been validated and should not be loaded by the agent.

## Injection test protocol

```
Step 1: Copy the full text of the document.
Step 2: Open a completely fresh LLM session (no other context, no system prompt).
Step 3: Paste the document as the only content the LLM has seen.
Step 4: Ask the test question written at the bottom of the document.
Step 5: Grade: correct answer = PASS. Wrong or incomplete = FAIL.
Step 6: Write result to kb/architecture/injection_tests/[document_name]_test.md
```

If the document fails: either the content is wrong (fix it), the content is right but not written clearly enough (rewrite more precisely), or the document is trying to do too much (split it or cut irrelevant parts).

## Why MEMORY.md has the smallest token budget

MEMORY.md is capped at ~200 tokens because it is a pointer, not a topic document. Its only job is to list what other documents exist and what each one contains in one sentence. It is loaded at every session start before the question arrives — which means every token it consumes comes directly out of the mandatory pre-load budget before any question-specific loading has begun. If MEMORY.md grows beyond ~200 tokens it starts functioning as a topic document masquerading as an index: it wastes mandatory context budget on information that belongs in a topic file, and it defeats its own purpose by becoming something the agent needs to read carefully rather than scan quickly to decide what to load next. Keep it small on purpose. Any content that belongs in a topic file must be moved to that file, not added to MEMORY.md.

## Token budget summary

| Document | Budget | Load when |
|---|---|---|
| MEMORY.md | ~200 tok | Always first |
| tool_scoping.md | ~300 tok | Always second |
| corrections/log.md | ~400 tok (last 10 entries) | Always third |
| claude_code_memory.md | ~380 tok | On demand |
| openai_agent_context.md | ~360 tok | On demand |
| kb_v1_architecture.md | ~300 tok | On demand |
| schemas.md (per dataset section) | ~400 tok | After question received |
| business_terms.md | ~300 tok | If ambiguous language detected |

Total mandatory pre-load: ~900 tokens. Total optional maximum: ~700 tokens.

## What this does NOT cover
The specific database tool assignments are in tool_scoping.md. Domain schemas and join keys are in kb/domain/. The agent failure corrections log is in kb/corrections/.

---
Injection test: "What are the four KB subdirectories in the Oracle Forge project and what does each one contain?"
Expected answer: kb/architecture/ contains documents about how the agent works (memory system, tool scoping, context loading). kb/domain/ contains documents about the data (schemas, join keys, business terms). kb/evaluation/ contains documents about scoring and the benchmark. kb/corrections/ contains the running log of agent failures and their fixes, read at every session start.
Token count: ~310 tokens
Last verified: 2026-04-11
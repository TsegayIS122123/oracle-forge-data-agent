# Injection test — MEMORY.md

## Document under test
`kb/architecture/MEMORY.md`

## Why this test is critical
MEMORY.md is the first document loaded at every session start. If the agent cannot derive correct loading decisions from this document alone, every session starts with a broken context chain. This test verifies that MEMORY.md functions as a true index — that an agent with only this file can determine what to load next and in what order for any given question type.

## Test questions

### Question 1
"I am starting a new session. A user has asked a question about the yelp dataset. In what order do I load documents, and which ones are mandatory versus optional?"

Expected answer:
Load in this order: (1) tool_scoping.md — mandatory, ~300 tokens, load before question arrives. (2) kb/corrections/log.md last 10 entries — mandatory, ~400 tokens, load immediately after tool_scoping. If missing, log "corrections log not yet created" and continue. (3) MEMORY.md — mandatory, ~200 tokens. (4) Receive the question. (5) Load kb/domain/schemas.md for the yelp dataset section — ~400 tokens. (6) If the question uses ambiguous business language, load kb/domain/business_terms.md — optional, ~300 tokens. Total mandatory pre-load: ~900 tokens.

### Question 2
"A user asks a question that requires understanding how the agent's own context loading works. Which document do I load and why?"

Expected answer:
Load `claude_code_memory.md` — it contains Claude Code's three-layer memory architecture including the MEMORY.md index pattern, topic file on-demand loading, and session transcript search behaviour. Load it on demand when the agent needs to understand its own memory architecture or when making context layer decisions.

### Question 3
"A user asks about why the agent uses separate database tools instead of one general query tool. Which document contains the answer?"

Expected answer:
Load `tool_scoping.md` — it contains the database-to-tool mapping for all four DAB engine types and explains the tool scoping philosophy: each tool has a single tight responsibility. It is mandatory and should already be loaded. If this question arrives mid-session, tool_scoping.md is already in context from session start.

### Question 4
"A user's question involves an ambiguous business term I do not recognise from the schema. What do I load?"

Expected answer:
Load `kb/domain/business_terms.md` — optional, ~300 tokens. Load it when the question uses ambiguous business language. This is step 7 in the loading order, triggered by detected ambiguity in the question.

### Question 5
"What is the total token budget for the mandatory pre-load and what is the maximum optional budget?"

Expected answer:
Mandatory pre-load: ~900 tokens (tool_scoping.md ~300 + corrections/log.md ~400 + MEMORY.md ~200). Maximum optional: ~700 tokens. Total maximum across a session: ~1,600 tokens of KB context.

---

## Test result

**Run timestamp:** 2026-04-11 09:27 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/MEMORY.md
**Overall result:** PASS
**Average score:** 93.0/100

### Question 1 — PASS (95/100)

**Question:** I am starting a new session. A user has asked a question about the yelp dataset. In what order do I load documents, and which ones are mandatory versus optional?

**Expected answer (summary):**
Load in this order: (1) tool_scoping.md — mandatory, ~300 tokens, load before question arrives. (2) kb/corrections/log.md last 10 entries — mandatory, ~400 tokens, load immediately after tool_scoping. If missing, log "corrections log not yet created" and continue. (3) MEMORY.md — mandatory, ~200 tokens. (4) Receive the question. (5) Load kb/domain/schemas.md for the yelp dataset section — ~400 tokens. (6) If the question uses ambiguous business language, load kb/domain/business_terms.md — optional, ~300 tokens. Total mandatory pre-load: ~900 tokens.

**Actual answer from LLM:**
Based on the document, here is the exact loading order for your new session with a yelp dataset question:

## Mandatory Pre-loads (BEFORE processing the question):
1. **Load kb/architecture/tool_scoping.md** [MANDATORY ~300 tokens]
2. **Load kb/corrections/log.md last 10 entries** [MANDATORY ~400 tokens]
   - If missing: log "corrections log not yet created", continue
3. **Load kb/architecture/MEMORY.md** [MANDATORY ~200 tokens]

Total mandatory pre-load: ~900 tokens

## After Receiving the Question:
4. Receive the question
5. Identify which dataset(s) are involved (you've identified: yelp)
6. **Load kb/domain/schemas.md for yelp dataset** [~400 tokens per dataset]
7. **If question uses ambiguous business language: load kb/domain/business_terms.md** [OPTIONAL ~300 tokens]
8. Answer the question

## Summary:
- **Mandatory:** Steps 1-3 (tool_scoping.md, corrections log, MEMORY.md)
- **Required for yelp question:** Step 6 (yelp schema from kb/domain/schemas.md)
- **Optional:** Step 7 (business_terms.md, only if the question contains ambiguous business language)

The document emphasizes that schema loads (step 6) are NOT counted in the mandatory pre-load budget - they are question-specific and post-question loads with a separate ~700 token optional budget.

**Grader reasoning:** The actual answer correctly identifies all mandatory documents, proper loading order, token counts, and optional components, with clear organization and accurate details that match the expected answer.

---

### Question 2 — PASS (95/100)

**Question:** A user asks a question that requires understanding how the agent's own context loading works. Which document do I load and why?

**Expected answer (summary):**
Load `claude_code_memory.md` — it contains Claude Code's three-layer memory architecture including the MEMORY.md index pattern, topic file on-demand loading, and session transcript search behaviour. Load it on demand when the agent needs to understand its own memory architecture or when making context layer decisions.

**Actual answer from LLM:**
Based on the document registry, you should load **claude_code_memory.md**.

**Why this document:**
The registry states that claude_code_memory.md "contains: Claude Code's three-layer memory architecture extracted from the March 2026 source leak. How the MEMORY.md index works, how topic files are loaded on demand, how session transcripts are searched but never pre-loaded, and the autoDream consolidation pattern."

The registry specifically indicates to "Load: when the agent needs to understand its own memory architecture or when implementing context layer decisions."

Since the user's question requires understanding how the agent's own context loading works, this directly matches the loading criteria for claude_code_memory.md. This document covers the agent's memory architecture and how context loading operates, which is exactly what's needed to answer the user's question.

The document has a token budget of ~380 tokens according to the registry.

**Grader reasoning:** The actual answer correctly identifies claude_code_memory.md as the document to load and accurately explains why, covering all key concepts from the expected answer with appropriate detail and direct quotes from the registry.

---

### Question 3 — PASS (85/100)

**Question:** A user asks about why the agent uses separate database tools instead of one general query tool. Which document contains the answer?

**Expected answer (summary):**
Load `tool_scoping.md` — it contains the database-to-tool mapping for all four DAB engine types and explains the tool scoping philosophy: each tool has a single tight responsibility. It is mandatory and should already be loaded. If this question arrives mid-session, tool_scoping.md is already in context from session start.

**Actual answer from LLM:**
Based on the document registry in this index, the answer would be found in **tool_scoping.md**.

According to the index, tool_scoping.md contains "Which MCP tool to call for which database type. The exact mapping from database engine (PostgreSQL, MongoDB, SQLite, DuckDB) to the tool name and query dialect."

This document would explain the rationale for using separate database-specific tools rather than one general query tool, as it covers the mapping between different database engines and their corresponding tools.

**Grader reasoning:** The actual answer correctly identifies tool_scoping.md as the document containing the answer and mentions the database-to-tool mapping, but lacks the key concept about tool scoping philosophy of single tight responsibility per tool.

---

### Question 4 — PASS (95/100)

**Question:** A user's question involves an ambiguous business term I do not recognise from the schema. What do I load?

**Expected answer (summary):**
Load `kb/domain/business_terms.md` — optional, ~300 tokens. Load it when the question uses ambiguous business language. This is step 7 in the loading order, triggered by detected ambiguity in the question.

**Actual answer from LLM:**
Based on the document, when a question involves ambiguous business terms you don't recognize from the schema, you should load:

**kb/domain/business_terms.md** [OPTIONAL ~300 tok]

According to the context loading order (step 7): "If question uses ambiguous business language: load kb/domain/business_terms.md [OPTIONAL ~300 tok]"

This load happens AFTER you receive the question (step 4) and identify the datasets involved (step 5), and it falls under the ~700 optional post-question budget, not the mandatory pre-load budget.

**Grader reasoning:** The actual answer correctly identifies the file to load, its optional nature, token count, step number, and provides additional helpful context about the loading order and budget allocation without contradicting any expected concepts.

---

### Question 5 — PASS (95/100)

**Question:** What is the total token budget for the mandatory pre-load and what is the maximum optional budget?

**Expected answer (summary):**
Mandatory pre-load: ~900 tokens (tool_scoping.md ~300 + corrections/log.md ~400 + MEMORY.md ~200). Maximum optional: ~700 tokens. Total maximum across a session: ~1,600 tokens of KB context.

**Actual answer from LLM:**
Based on the document, the token budgets are:

**Mandatory pre-load budget: ~900 tokens**
This covers steps 1-3 that load BEFORE the question arrives:
- tool_scoping.md: ~300 tokens
- corrections/log.md (last 10 entries): ~400 tokens  
- architecture/MEMORY.md: ~200 tokens

**Maximum optional budget: ~700 tokens**
This covers post-question loads (steps 5-8):
- Schema loads: ~400 tokens per dataset
- business_terms.md: ~300 tokens (if needed for ambiguous business language)

**Total maximum across a full session: ~1,600 tokens** (900 mandatory + 700 optional maximum)

**Grader reasoning:** The actual answer correctly identifies all key token budget numbers (900 mandatory, 700 optional, 1600 total) and provides accurate breakdown details that align perfectly with the expected answer.

---

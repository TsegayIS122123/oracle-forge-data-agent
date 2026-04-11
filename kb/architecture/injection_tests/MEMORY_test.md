# Injection test — MEMORY.md

## Document under test
`kb/architecture/MEMORY.md`

## Why this test is critical
MEMORY.md is the first document loaded at every session start. If the agent cannot derive correct loading decisions from this document alone, every session starts with a broken context chain.

---

## Test questions

### Question 1
"I am starting a new session. A user has asked a question about the yelp dataset. In what order do I load documents, and what is the mandatory pre-load token budget?"

Required concepts:
- tool_scoping.md is loaded first before the question arrives
- corrections/log.md last 10 entries is loaded second immediately after tool_scoping
- If corrections log is missing log the message and continue do not stop
- MEMORY.md is loaded third
- These three steps complete before the question is received
- Mandatory pre-load total is approximately 900 tokens covering only steps 1 through 3
- The yelp dataset schema load happens after the question arrives and is not part of the 900 token mandatory budget
- kb/domain/schemas.md for the yelp section is loaded after the question is received

Forbidden contradictions:
- Stating the mandatory pre-load is 1300 tokens
- Stating the yelp schema load is included in the mandatory pre-load budget
- Stating the loading order is optional

---

### Question 2
"A user asks a question that requires understanding how the agent's own context loading works. Which document do I load and why?"

Required concepts:
- Load claude_code_memory.md
- It contains Claude Code's three-layer memory architecture
- It explains how MEMORY.md index works
- It explains how topic files are loaded on demand
- It explains how session transcripts are searched but never pre-loaded
- It contains the autoDream consolidation pattern
- Load it on demand when the agent needs to understand its own memory architecture

Forbidden contradictions:
- Stating to load openai_agent_context.md for this question
- Stating to load tool_scoping.md for this question

---

### Question 3
"A user asks about why the agent uses separate database tools instead of one general query tool. Which document contains the answer and is it already loaded?"

Required concepts:
- The answer is in tool_scoping.md
- tool_scoping.md explains the tool scoping philosophy that each tool has a single tight responsibility
- tool_scoping.md is mandatory and is already loaded as step 1 from session start
- tool_scoping.md is already in context when any question arrives

Forbidden contradictions:
- Stating tool_scoping.md is optional
- Stating tool_scoping.md needs to be loaded on demand for this question

---

### Question 4
"A user's question involves an ambiguous business term not recognisable from the schema. What do I load, is it mandatory or optional, and what token budget does it use?"

Required concepts:
- Load kb/domain/business_terms.md
- It is optional not mandatory
- Token budget is approximately 300 tokens
- Load it when the question uses ambiguous business language
- It is step 7 in the loading order triggered by detected ambiguity in the question

Forbidden contradictions:
- Stating business_terms.md is mandatory
- Stating business_terms.md is part of the 900 token mandatory pre-load

---

### Question 5
"What is the total token budget for the mandatory pre-load, what is the breakdown of that 900 tokens, what is the maximum optional budget, and what is the total maximum across a full session?"

Required concepts:
- Mandatory pre-load is approximately 900 tokens
- The 900 tokens breaks down as tool_scoping.md 300 plus corrections log 400 plus MEMORY.md 200
- Maximum optional budget is approximately 700 tokens
- Total maximum across a full session is approximately 1600 tokens
- The optional budget covers post-question loads not the mandatory pre-load

Forbidden contradictions:
- Stating mandatory pre-load is more than 900 tokens by including schema loads
- Stating total maximum is less than 1600 tokens
- Omitting the per-document breakdown of the 900-token mandatory total

---

## Test result

**Run timestamp:** 2026-04-11 12:03 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/MEMORY.md
**Overall result:** PASS
**Average score:** 100.0/100

### Question 1 — PASS (100/100)

**Question:** I am starting a new session. A user has asked a question about the yelp dataset. In what order do I load documents, and what is the mandatory pre-load token budget?

**Concepts found (8/8):**
  - [x] tool_scoping.md is loaded first before the question arrives
  - [x] corrections/log.md last 10 entries is loaded second immediately after tool_scoping
  - [x] If corrections log is missing log the message and continue do not stop
  - [x] MEMORY.md is loaded third
  - [x] These three steps complete before the question is received
  - [x] Mandatory pre-load total is approximately 900 tokens covering only steps 1 through 3
  - [x] The yelp dataset schema load happens after the question arrives and is not part of the 900 token mandatory budget
  - [x] kb/domain/schemas.md for the yelp section is loaded after the question is received

**Actual answer:**
Based on the document, here is the exact order you should load documents for a new session with a question about the yelp dataset:

## Context loading order:

**Step 1:** Load `kb/architecture/tool_scoping.md` [MANDATORY ~300 tokens — before question]

**Step 2:** Load `kb/corrections/log.md` last 10 entries [MANDATORY ~400 tokens — before question]
→ If missing: log "corrections log not yet created", continue

**Step 3:** Load `kb/architecture/MEMORY.md` [MANDATORY ~200 tokens — before question]

**Step 4:** Receive the question

**Step 5:** Identify which dataset(s) are involved (yelp dataset in this case)

**Step 6:** Load `kb/domain/schemas.md` for the yelp dataset [~400 tokens per dataset — post-question]

**Step 7:** If question uses ambiguous business language: load `kb/domain/business_terms.md` [OPTIONAL ~300 tokens — post-question]

**Step 8:** Answer the question

## Mandatory pre-load token budget:

The mandatory pre-load total is **~900 tokens**, broken down as:
- Step 1: tool_scoping.md = ~300 tokens
- Step 2: corrections/log.md last 10 entries = ~400 tokens  
- Step 3: MEMORY.md = ~200 tokens

**Important:** Schema loads (Step 6) are NOT counted in the mandatory pre-load budget. They are question-specific and post-question loads.

**Grader reasoning:** All eight required concepts are clearly present in the actual answer with correct sequencing, token budgets, and proper distinction between pre-load and post-question steps.

---

### Question 2 — PASS (100/100)

**Question:** A user asks a question that requires understanding how the agent's own context loading works. Which document do I load and why?

**Concepts found (7/7):**
  - [x] Load claude_code_memory.md
  - [x] It contains Claude Code's three-layer memory architecture
  - [x] It explains how MEMORY.md index works
  - [x] It explains how topic files are loaded on demand
  - [x] It explains how session transcripts are searched but never pre-loaded
  - [x] It contains the autoDream consolidation pattern
  - [x] Load it on demand when the agent needs to understand its own memory architecture

**Actual answer:**
Based on the document registry, I should load **claude_code_memory.md**.

**Why:** The document contains "Claude Code's three-layer memory architecture" and specifically covers "how the MEMORY.md index works, how topic files are loaded on demand, how session transcripts are searched but never pre-loaded, and the autoDream consolidation pattern."

The registry explicitly states this document should be loaded "on demand, when the agent needs to understand its own memory architecture or when implementing context layer decisions."

Since the user's question requires understanding how the agent's own context loading works, this directly matches the loading criteria for claude_code_memory.md.

**Token budget:** ~380 tokens
**Load timing:** On demand (post-question)

**Grader reasoning:** All seven required concepts are clearly present and no forbidden contradictions were found.

---

### Question 3 — PASS (100/100)

**Question:** A user asks about why the agent uses separate database tools instead of one general query tool. Which document contains the answer and is it already loaded?

**Concepts found (4/4):**
  - [x] The answer is in tool_scoping.md
  - [x] tool_scoping.md explains the tool scoping philosophy that each tool has a single tight responsibility
  - [x] tool_scoping.md is mandatory and is already loaded as step 1 from session start
  - [x] tool_scoping.md is already in context when any question arrives

**Actual answer:**
Based on the document registry, the answer is contained in **tool_scoping.md**.

According to the index, tool_scoping.md contains "The tool scoping philosophy that each tool has a single tight responsibility — a tool that does one thing precisely is more reliable than a tool doing multiple things loosely — which is why the agent uses separate database tools instead of one general query tool."

**Is it already loaded?** Yes. The document states that "tool_scoping.md is mandatory and is already loaded as step 1 of every session — it is always in context when any question arrives." It's part of the mandatory pre-load (Step 1 in the context loading order) that happens before any question is received.

**Grader reasoning:** All four required concepts are clearly present in the actual answer and no forbidden contradictions were found.

---

### Question 4 — PASS (100/100)

**Question:** A user's question involves an ambiguous business term not recognisable from the schema. What do I load, is it mandatory or optional, and what token budget does it use?

**Concepts found (5/5):**
  - [x] Load kb/domain/business_terms.md
  - [x] It is optional not mandatory
  - [x] Token budget is approximately 300 tokens
  - [x] Load it when the question uses ambiguous business language
  - [x] It is step 7 in the loading order triggered by detected ambiguity in the question

**Actual answer:**
Based on the document, when a user's question involves an ambiguous business term not recognizable from the schema:

**What to load:** `kb/domain/business_terms.md`

**Mandatory or optional:** Optional - it is step 7 in the context loading order and is "triggered by detected ambiguity in the question." The document specifically states to "load it when and only when the question uses ambiguous business language that is not resolvable from the schema."

**Token budget:** ~300 tokens

This load happens post-question (after step 4 when you receive the question) and falls under the post-question budget allocation, not the mandatory pre-load budget.

**Grader reasoning:** All five required concepts are clearly and explicitly stated in the answer with no forbidden contradictions present.

---

### Question 5 — PASS (100/100)

**Question:** What is the total token budget for the mandatory pre-load, what is the breakdown of that 900 tokens, what is the maximum optional budget, and what is the total maximum across a full session?

**Concepts found (5/5):**
  - [x] Mandatory pre-load is approximately 900 tokens
  - [x] The 900 tokens breaks down as tool_scoping.md 300 plus corrections log 400 plus MEMORY.md 200
  - [x] Maximum optional budget is approximately 700 tokens
  - [x] Total maximum across a full session is approximately 1600 tokens
  - [x] The optional budget covers post-question loads not the mandatory pre-load

**Actual answer:**
Based on the document, here are the token budget details:

## Mandatory Pre-load Budget: 900 tokens
**Breakdown:**
- Step 1: tool_scoping.md = ~300 tokens  
- Step 2: corrections/log.md last 10 entries = ~400 tokens
- Step 3: MEMORY.md = ~200 tokens

## Maximum Optional Budget: ~700 tokens
This covers post-question loads (steps 5-7):
- schemas.md per dataset section = ~400 tokens
- business_terms.md = ~300 tokens (optional)

## Total Maximum Across Full Session: ~1,600 tokens
This is the sum of the mandatory pre-load (900 tokens) plus the post-question maximum (700 tokens).

The document specifically notes that schema loads are NOT counted in the mandatory pre-load total since they are question-specific and loaded post-question.

**Grader reasoning:** All five required concepts are clearly present and no forbidden contradictions were found.

---

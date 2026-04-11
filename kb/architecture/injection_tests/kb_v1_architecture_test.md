# Injection test — kb_v1_architecture.md

## Document under test
`kb/architecture/kb_v1_architecture.md`

## Why this test is critical
This document defines the rules that govern the entire KB system — token budgets, the Karpathy discipline, injection test protocol, and what each subdirectory contains. If the agent cannot derive the correct subdirectory for a given type of knowledge from this document alone, it will attempt to load the wrong file when it needs information — wasting context budget and potentially loading nothing useful.

## Test questions

### Question 1
"What are the four KB subdirectories in the Oracle Forge project and what type of information belongs in each one?"

Expected answer:
`kb/architecture/` contains documents about how the agent itself works: memory architecture, tool scoping rules, context loading order, and KB structural overview. These change when the agent architecture changes, not when datasets change. `kb/domain/` contains documents about the data the agent works with: schema descriptions per DAB dataset, join key formats, unstructured field inventory, and business term definitions. These change when new datasets are loaded or failure patterns reveal schema misunderstandings. `kb/evaluation/` contains documents about scoring and the benchmark: DAB query format, pass@1 scoring method, submission requirements, and the four DAB failure categories. `kb/corrections/` contains the running structured log of agent failures with what was wrong and the correct approach — the self-learning loop.

### Question 2
"An Intelligence Officer wants to add a new document to the KB. What is the exact injection test protocol they must follow before committing it?"

Expected answer:
Step 1: Copy the full text of the document. Step 2: Open a completely fresh LLM session with no other context and no system prompt. Step 3: Paste the document as the only content the LLM has seen. Step 4: Ask the test question written at the bottom of the document. Step 5: Grade the result — correct answer is PASS, wrong or incomplete is FAIL. Step 6: Write the result to `kb/architecture/injection_tests/[document_name]_test.md`. Documents that fail must be either rewritten more precisely, corrected, or split into smaller documents. A document without a test result has not been validated and must not be loaded by the agent.

### Question 3
"What is the Karpathy discipline and how does it differ from standard documentation practice?"

Expected answer:
The Karpathy discipline is: removal, not accumulation. Every document must be minimal and precise — tested by injection, not just reviewed by a human. Standard documentation grows over time as more information is added. The Karpathy discipline requires removing everything the LLM already knows from pretraining and keeping only what is specific to DAB, these databases, and this agent. A KB that grows without being tested becomes noise that degrades the agent — the LLM wastes context budget loading information that does not help it answer questions. The test for every sentence is: if the agent read only this sentence with no other context, could it take the correct action?

### Question 4
"Which document has the smallest token budget and why?"

Expected answer:
MEMORY.md has the smallest budget at ~200 tokens because it is loaded at every session start before the question arrives. Its sole purpose is to be a pointer — listing what other documents exist and what they contain. If MEMORY.md grows beyond ~200 tokens it becomes a topic document masquerading as an index, which defeats its purpose and wastes mandatory context budget before any question-specific loading has even started.

---

## Test result

**Run timestamp:** 2026-04-11 09:28 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/kb_v1_architecture.md
**Overall result:** PASS
**Average score:** 95.0/100

### Question 1 — PASS (95/100)

**Question:** What are the four KB subdirectories in the Oracle Forge project and what type of information belongs in each one?

**Expected answer (summary):**
`kb/architecture/` contains documents about how the agent itself works: memory architecture, tool scoping rules, context loading order, and KB structural overview. These change when the agent architecture changes, not when datasets change. `kb/domain/` contains documents about the data the agent works with: schema descriptions per DAB dataset, join key formats, unstructured field inventory, and business term definitions. These change when new datasets are loaded or failure patterns reveal schema misunderstandings. `kb/evaluation/` contains documents about scoring and the benchmark: DAB query format, pass@1 scoring method, submission requirements, and the four DAB failure categories. `kb/corrections/` contains the running structured log of agent failures with what was wrong and the correct approach — the self-learning loop.

**Actual answer from LLM:**
Based on the document, the four KB subdirectories in the Oracle Forge project are:

**kb/architecture/** - Contains documents about how the agent itself works, including the memory architecture, tool scoping rules, context loading order, and structural overviews. These documents are written for the agent about the agent and change when the agent architecture changes.

**kb/domain/** - Contains documents about the data the agent works with, including schema descriptions per DAB dataset, join key formats across database systems, unstructured field inventory, and business term definitions. These documents change when datasets are loaded or when domain understanding needs correction.

**kb/evaluation/** - Contains documents about how the agent is scored and what the benchmark requires, including DAB query format, pass@1 scoring method, submission requirements, and the four DAB failure categories.

**kb/corrections/** - Contains the running structured log of agent failures as part of the self-learning loop. The agent reads the last 10 entries at session start, and new entries are written after every observed failure.

**Grader reasoning:** The actual answer accurately covers all four subdirectories and their purposes with correct details, only missing minor specifics like 'schema misunderstandings' in the domain section.

---

### Question 2 — PASS (95/100)

**Question:** An Intelligence Officer wants to add a new document to the KB. What is the exact injection test protocol they must follow before committing it?

**Expected answer (summary):**
Step 1: Copy the full text of the document. Step 2: Open a completely fresh LLM session with no other context and no system prompt. Step 3: Paste the document as the only content the LLM has seen. Step 4: Ask the test question written at the bottom of the document. Step 5: Grade the result — correct answer is PASS, wrong or incomplete is FAIL. Step 6: Write the result to `kb/architecture/injection_tests/[document_name]_test.md`. Documents that fail must be either rewritten more precisely, corrected, or split into smaller documents. A document without a test result has not been validated and must not be loaded by the agent.

**Actual answer from LLM:**
Based on the document, the exact injection test protocol an Intelligence Officer must follow is:

```
Step 1: Copy the full text of the document.
Step 2: Open a completely fresh LLM session (no other context, no system prompt).
Step 3: Paste the document as the only content the LLM has seen.
Step 4: Ask the test question written at the bottom of the document.
Step 5: Grade: correct answer = PASS. Wrong or incomplete = FAIL.
Step 6: Write result to kb/architecture/injection_tests/[document_name]_test.md
```

If the document fails the test, they must either: fix the content if it's wrong, rewrite it more precisely if it's right but unclear, or split/cut it if the document is trying to do too much.

The document also states that "Documents that have not been injection-tested have not been validated and should not be loaded by the agent," emphasizing that this testing is mandatory before committing any new KB document.

**Grader reasoning:** The actual answer captures all key concepts from the expected answer with accurate details and proper formatting, only missing the minor detail about correcting documents that are factually wrong.

---

### Question 3 — PASS (95/100)

**Question:** What is the Karpathy discipline and how does it differ from standard documentation practice?

**Expected answer (summary):**
The Karpathy discipline is: removal, not accumulation. Every document must be minimal and precise — tested by injection, not just reviewed by a human. Standard documentation grows over time as more information is added. The Karpathy discipline requires removing everything the LLM already knows from pretraining and keeping only what is specific to DAB, these databases, and this agent. A KB that grows without being tested becomes noise that degrades the agent — the LLM wastes context budget loading information that does not help it answer questions. The test for every sentence is: if the agent read only this sentence with no other context, could it take the correct action?

**Actual answer from LLM:**
Based on the document, the Karpathy method is a discipline focused on "minimum content, maximum precision" where "the discipline is removal, not accumulation."

It differs from standard documentation practice in several key ways:

1. **Removal over accumulation**: Instead of continuously adding documentation, the focus is on removing content that doesn't pass strict testing.

2. **Injection testing requirement**: Every document must pass an "injection test" - it's pasted into a fresh LLM session as the only context, asked a test question, and graded. Documents that fail are revised or removed, never kept.

3. **Exclude common knowledge**: Remove everything the LLM already knows from pretraining - only include what is specific to DAB, the databases, and the agent.

4. **Strict token budgets**: Every document has a stated token budget that cannot be exceeded.

5. **Mandatory validation**: Documents that haven't been injection-tested are considered unvalidated and shouldn't be loaded by the agent.

The core philosophy is that "a KB that grows without being tested becomes noise that degrades the agent." The goal is that an agent loading only the relevant KB documents should answer questions correctly - not an agent that loads everything. This contrasts with typical documentation practices that tend to accumulate information without strict testing or removal processes.

**Grader reasoning:** The actual answer comprehensively covers all key concepts from the expected answer with accurate details and good organization, only missing the specific sentence-level test criterion.

---

### Question 4 — PASS (95/100)

**Question:** Which document has the smallest token budget and why?

**Expected answer (summary):**
MEMORY.md has the smallest budget at ~200 tokens because it is loaded at every session start before the question arrives. Its sole purpose is to be a pointer — listing what other documents exist and what they contain. If MEMORY.md grows beyond ~200 tokens it becomes a topic document masquerading as an index, which defeats its purpose and wastes mandatory context budget before any question-specific loading has even started.

**Actual answer from LLM:**
According to the document, MEMORY.md has the smallest token budget at ~200 tokens.

The reason is that MEMORY.md is a pointer, not a topic document. Its only job is to list what other documents exist and what each one contains in one sentence. It is loaded at every session start before the question arrives, which means every token it consumes comes directly out of the mandatory pre-load budget before any question-specific loading has begun. 

If MEMORY.md grows beyond ~200 tokens, it starts functioning as a topic document masquerading as an index, which wastes mandatory context budget on information that belongs in a topic file and defeats its own purpose by becoming something the agent needs to read carefully rather than scan quickly to decide what to load next. It's kept small on purpose so it can function as a quick reference index rather than detailed content.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer and provides additional accurate detail about MEMORY.md's purpose and constraints without contradicting the expected response.

---

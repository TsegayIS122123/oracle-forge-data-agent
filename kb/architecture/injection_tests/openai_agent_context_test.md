# Injection test — openai_agent_context.md

## Document under test
`kb/architecture/openai_agent_context.md`

## Why this test is critical
This document contains the conceptual architecture that justifies the Oracle Forge agent's three mandatory context layers. If the agent cannot correctly explain the six layers and map them to Oracle Forge equivalents from this document alone, it does not understand why its own architecture exists. This causes incorrect decisions under failure: the agent may skip loading the corrections log, fail to detect domain term ambiguity, or not perform runtime schema inspection when needed.

## Test questions

### Question 1
"What is Layer 5 in OpenAI's six-layer context architecture, what problem does it solve, and what is the Oracle Forge equivalent?"

Expected answer:
Layer 5 is the learning memory. It stores corrections and nuances discovered in previous conversations and applies them automatically to future requests. It solves the problem of repeated failures — the agent makes the same mistake in every session unless past corrections are surfaced. OpenAI measured this layer's impact directly: a query that took 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled. The Oracle Forge equivalent is `kb/corrections/log.md` — the running structured log of `[query that failed] → [what was wrong] → [correct approach]`, with the last 10 entries loaded at every session start.

### Question 2
"What is Codex Enrichment and what does it reveal that basic schema metadata does not?"

Expected answer:
Codex Enrichment is OpenAI's Layer 3. It is a daily asynchronous process where Codex crawls the codebase that generates each data table and derives a deeper definition from the pipeline code itself. Pipeline logic captures upstream and downstream dependencies, ownership, granularity, join keys, filtering assumptions, and freshness guarantees — none of which appear in SQL schema metadata or column names. Example: the code may reveal that a table filters to only US users before aggregating, which is invisible in the schema. This matters because many tables look identical in their schema but differ critically in what data they actually contain.

### Question 3
"What is the closed-loop self-correction pattern and how does it differ from standard error handling?"

Expected answer:
The closed-loop self-correction pattern means the agent evaluates its own intermediate results during execution — not just at the end. If a result looks wrong (zero rows from an expected join, a count that seems implausible, a metric that contradicts a known baseline), the agent investigates the cause, adjusts its approach, and retries. It does not return the suspicious result to the user. It carries the correction forward as a log entry so the same mistake does not recur in future sessions. This is not error handling — error handling reacts to exceptions. Self-correction is the agent evaluating the quality of its own reasoning mid-execution, even when no exception is raised.

### Question 4
"Why does the core problem in OpenAI's data agent architecture exist, and how does it apply to the DataAgentBench challenge?"

Expected answer:
The core problem is that finding the right table is the hardest sub-problem — not query generation. Many tables look similar on the surface but differ critically: one table includes only logged-in users while another includes everyone; one captures only first-party traffic while another captures everything. Without layered context, the agent picks the wrong table and produces a wrong answer that looks correct — no error, just wrong numbers. This applies directly to DataAgentBench: multiple databases in each dataset contain similarly-named tables with different semantics, inconsistently-formatted join keys, and domain-specific business terms that are not derivable from the schema. The six-layer architecture exists specifically to give the agent the context to distinguish these cases.

### Question 5
"What are the three engineering lessons OpenAI learned during development of their data agent?"

Expected answer:
First: tool consolidation matters — overlapping tools with redundant functionality confuse the agent. Restrict to one tool per database type with tight domain boundaries. Second: less prescriptive prompting works better — rigid step-by-step instructions pushed the agent down wrong paths when the situation did not match the script. Higher-level guidance combined with model reasoning produces more robust results. Third: code reveals what metadata hides — pipeline logic contains assumptions (filtering, aggregation logic, business intent) that never surface in table schemas. Crawling the codebase that generates tables provides more useful context than reading the tables themselves.

---

## Test result

**Run timestamp:** 2026-04-11 09:18 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/openai_agent_context.md
**Overall result:** PASS
**Average score:** 95.0/100

### Question 1 — PASS (95/100)

**Question:** What is Layer 5 in OpenAI's six-layer context architecture, what problem does it solve, and what is the Oracle Forge equivalent?

**Expected answer (summary):**
Layer 5 is the learning memory. It stores corrections and nuances discovered in previous conversations and applies them automatically to future requests. It solves the problem of repeated failures — the agent makes the same mistake in every session unless past corrections are surfaced. OpenAI measured this layer's impact directly: a query that took 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled. The Oracle Forge equivalent is `kb/corrections/log.md` — the running structured log of `[query that failed] → [what was wrong] → [correct approach]`, with the last 10 entries loaded at every session start.

**Actual answer from LLM:**
Based on the document, Layer 5 in OpenAI's six-layer context architecture is **Learning memory (self-correction loop)**.

**What it does:** The agent stores corrections and nuances discovered in previous conversations and applies them to future requests. For example, it might learn that "The join between the customer table and the transaction table requires zero-padding the customer ID to 5 digits" and store this as a correction to apply in future sessions.

**Problem it solves:** It reduces repeated failures from the same mistake by carrying forward institutional knowledge gained through experience. According to OpenAI's measurements, a query that took 22 minutes without memory dropped to 1 minute 22 seconds with memory enabled. The document states that "Memory is non-negotiable."

**Oracle Forge equivalent:** The equivalent is `kb/corrections/log.md` — a running structured log with the format `[query that failed] → [what was wrong] → [correct approach]`. The agent reads the last 10 entries at the start of every session to avoid repeating previous mistakes.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer with accurate details and clear structure, only losing minor points for slightly more verbose presentation.

---

### Question 2 — PASS (95/100)

**Question:** What is Codex Enrichment and what does it reveal that basic schema metadata does not?

**Expected answer (summary):**
Codex Enrichment is OpenAI's Layer 3. It is a daily asynchronous process where Codex crawls the codebase that generates each data table and derives a deeper definition from the pipeline code itself. Pipeline logic captures upstream and downstream dependencies, ownership, granularity, join keys, filtering assumptions, and freshness guarantees — none of which appear in SQL schema metadata or column names. Example: the code may reveal that a table filters to only US users before aggregating, which is invisible in the schema. This matters because many tables look identical in their schema but differ critically in what data they actually contain.

**Actual answer from LLM:**
Based on the document, Codex Enrichment is Layer 3 of OpenAI's six-layer context architecture. 

**What it is:** OpenAI crawls their codebase daily using Codex to derive each table's meaning from the pipeline code that generates it.

**What it reveals that basic schema metadata does not:** Pipeline logic captures assumptions, freshness guarantees, and business intent that never appear in SQL or metadata. The document gives a specific example: the code reveals that a table filters to only US users before aggregating — a fact that is invisible in the schema.

The document emphasizes this principle in the engineering lessons: "Code reveals what metadata hides: pipeline logic contains assumptions that never surface in table schemas. Reading the code that generates a table tells you more than reading the table's schema."

In the Oracle Forge context, this corresponds to reading the DAB query patterns and understanding what the queries assume about the data.

**Grader reasoning:** The actual answer captures all key concepts including Codex Enrichment as Layer 3, daily crawling process, pipeline logic revealing hidden assumptions like US-only filtering, and the core principle that code reveals what metadata hides, with only minor omissions of some technical details.

---

### Question 3 — PASS (95/100)

**Question:** What is the closed-loop self-correction pattern and how does it differ from standard error handling?

**Expected answer (summary):**
The closed-loop self-correction pattern means the agent evaluates its own intermediate results during execution — not just at the end. If a result looks wrong (zero rows from an expected join, a count that seems implausible, a metric that contradicts a known baseline), the agent investigates the cause, adjusts its approach, and retries. It does not return the suspicious result to the user. It carries the correction forward as a log entry so the same mistake does not recur in future sessions. This is not error handling — error handling reacts to exceptions. Self-correction is the agent evaluating the quality of its own reasoning mid-execution, even when no exception is raised.

**Actual answer from LLM:**
Based on the document, the closed-loop self-correction pattern is when the agent evaluates its own reasoning mid-execution rather than simply handling errors. Here's how it works:

**What it is:**
If an intermediate result looks wrong (zero rows from an expected join, a count that seems too high, a metric that contradicts a known baseline), the agent does not return the result. Instead, it investigates by checking the join keys, filter conditions, and whether the correct table was selected. Then it adjusts its approach and retries, carrying the finding forward as a correction log entry so the same mistake doesn't recur.

**How it differs from standard error handling:**
The document explicitly states: "This is not error handling. It is the agent evaluating its own reasoning mid-execution." 

Standard error handling typically responds to system errors or exceptions after they occur. In contrast, the closed-loop self-correction pattern involves the agent proactively detecting when results don't make logical sense and investigating the reasoning process itself before concluding the task.

**Oracle Forge implementation:**
The Oracle Forge agent implements this in `self_corrector.py`, which detects execution failure, diagnoses which of four failure categories applies (wrong tool, wrong join key, unstructured text not extracted, domain term misunderstood), then retries with the correct approach.

**Grader reasoning:** The actual answer captures all key concepts from the expected answer including mid-execution evaluation, investigation and retry process, correction logging, and the clear distinction from standard error handling, plus adds relevant implementation details.

---

### Question 4 — PASS (95/100)

**Question:** Why does the core problem in OpenAI's data agent architecture exist, and how does it apply to the DataAgentBench challenge?

**Expected answer (summary):**
The core problem is that finding the right table is the hardest sub-problem — not query generation. Many tables look similar on the surface but differ critically: one table includes only logged-in users while another includes everyone; one captures only first-party traffic while another captures everything. Without layered context, the agent picks the wrong table and produces a wrong answer that looks correct — no error, just wrong numbers. This applies directly to DataAgentBench: multiple databases in each dataset contain similarly-named tables with different semantics, inconsistently-formatted join keys, and domain-specific business terms that are not derivable from the schema. The six-layer architecture exists specifically to give the agent the context to distinguish these cases.

**Actual answer from LLM:**
According to the document, the core problem exists because **finding the right table across 70,000 datasets and 600 petabytes is the hardest sub-problem — not query generation**. 

The specific issue is that many tables look similar on the surface but have critical differences in their semantics:
- One table includes only logged-in users, another includes everyone
- One captures only first-party traffic, another captures everything

Without layered context, the agent picks the wrong table and produces a wrong answer that looks correct.

**How it applies to the DataAgentBench (DAB) challenge:**

The document states this is "the same problem the Oracle Forge agent faces on DAB: multiple databases, similar-looking schemas, different semantics." 

In the DAB context, the challenge is navigating multiple databases where tables may appear similar in their schema structure but contain fundamentally different data or have different business meanings. The agent needs the six-layer context architecture to distinguish between these seemingly similar but semantically different tables to avoid producing incorrect results that appear plausible on the surface.

**Grader reasoning:** The actual answer captures all key concepts from the expected answer including the core problem of table selection, specific examples of table differences, the issue of wrong but plausible-looking results, and how this applies to DataAgentBench with multiple databases and similar schemas having different semantics.

---

### Question 5 — PASS (95/100)

**Question:** What are the three engineering lessons OpenAI learned during development of their data agent?

**Expected answer (summary):**
First: tool consolidation matters — overlapping tools with redundant functionality confuse the agent. Restrict to one tool per database type with tight domain boundaries. Second: less prescriptive prompting works better — rigid step-by-step instructions pushed the agent down wrong paths when the situation did not match the script. Higher-level guidance combined with model reasoning produces more robust results. Third: code reveals what metadata hides — pipeline logic contains assumptions (filtering, aggregation logic, business intent) that never surface in table schemas. Crawling the codebase that generates tables provides more useful context than reading the tables themselves.

**Actual answer from LLM:**
Based on the document, OpenAI learned three key engineering lessons during development of their data agent:

1. **Tool consolidation matters**: Overlapping tools confuse the agent. They learned to restrict to one tool per database type with tight domain boundaries — following the same principle as Claude Code's tool scoping philosophy.

2. **Less prescriptive prompting**: Rigid step-by-step instructions pushed the agent down wrong paths when the situation didn't match the script. Higher-level guidance plus model reasoning produces more robust results.

3. **Code reveals what metadata hides**: Pipeline logic contains assumptions that never surface in table schemas. Reading the code that generates a table tells you more than reading the table's schema itself.

**Grader reasoning:** The actual answer captures all three key engineering lessons with accurate content and only minor acceptable wording differences, though it adds an unnecessary reference to Claude Code.

---

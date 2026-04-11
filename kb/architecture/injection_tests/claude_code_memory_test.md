# Injection test — claude_code_memory.md

## Document under test
`kb/architecture/claude_code_memory.md`

## Test questions

### Question 1
"What is the purpose of MEMORY.md in Claude Code's memory system, and what does the agent do with it at session start?"

Expected answer:
MEMORY.md is a small index file (~200 tokens) that lists all topic files with a one-sentence description of each. The agent reads it first at session start to know what knowledge is available, then uses it to decide which topic files to load next based on the current question. It is never more than ~200 tokens — growing it beyond this defeats its purpose.

### Question 2
"What is autoDream and when does it run?"

Expected answer:
autoDream is a background process that runs after sessions end. It reviews what was learned during the session — corrections made, successful patterns, new definitions discovered — and consolidates them back into the relevant topic files. Old, superseded information is removed. The topic file after consolidation is smaller and more precise. It is implemented in src/tasks/DreamTask/ and src/services/autoDream/ in the Claude Code source.

### Question 3
"Why does Claude Code use 40+ tools with tight domain boundaries instead of fewer general-purpose tools?"

Expected answer:
Each tool has a single, tight responsibility. A tool that does one thing precisely is more reliable than a tool that tries to do three things loosely. When a tool fails, the agent knows exactly which tool failed and why — because each tool does exactly one thing. This is the tool scoping philosophy from Claude Code's source: tight domain boundaries make failures diagnosable and recoverable.

### Question 4
"What are session transcripts in Claude Code's memory system and how are they accessed?"

Expected answer:
Session transcripts are logs of past agent runs. They are never pre-loaded into context — searching is cheap, pre-loading is expensive. The agent searches them only when a new question closely resembles a past one. This is enforced by the context window budget management in QueryEngine.ts.

---

## Test result

**Run timestamp:** 2026-04-11 09:18 UTC
**Model used:** anthropic/claude-sonnet-4
**Document tested:** kb/architecture/claude_code_memory.md
**Overall result:** PASS
**Average score:** 95.0/100

### Question 1 — PASS (95/100)

**Question:** What is the purpose of MEMORY.md in Claude Code's memory system, and what does the agent do with it at session start?

**Expected answer (summary):**
MEMORY.md is a small index file (~200 tokens) that lists all topic files with a one-sentence description of each. The agent reads it first at session start to know what knowledge is available, then uses it to decide which topic files to load next based on the current question. It is never more than ~200 tokens — growing it beyond this defeats its purpose.

**Actual answer from LLM:**
Based on the document, MEMORY.md serves as a small index file (~200 tokens, always loaded) in Claude Code's memory system. Its purpose is to list every other knowledge base document by name with a one-sentence description - it functions like a table of contents pointing to topic files rather than containing content itself.

At session start, the agent reads MEMORY.md first to know what knowledge is available, then uses it to decide what to load next. The agent uses this index to determine which topic files are relevant to the current question and loads only those specific topic files on demand, rather than loading all topic files upfront.

The document emphasizes that MEMORY.md is never more than ~200 tokens, as growing it beyond this defeats its purpose as a lightweight index for efficient knowledge discovery.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer with accurate details and good organization, only missing the explicit mention that the agent 'reads it first at session start' though this is implied in the explanation.

---

### Question 2 — PASS (95/100)

**Question:** What is autoDream and when does it run?

**Expected answer (summary):**
autoDream is a background process that runs after sessions end. It reviews what was learned during the session — corrections made, successful patterns, new definitions discovered — and consolidates them back into the relevant topic files. Old, superseded information is removed. The topic file after consolidation is smaller and more precise. It is implemented in src/tasks/DreamTask/ and src/services/autoDream/ in the Claude Code source.

**Actual answer from LLM:**
Based on the document, autoDream is a background process that runs after a session ends. It reviews what was learned during the session — including corrections made, successful query patterns, and new business term definitions discovered — and consolidates them back into the relevant topic files. 

During this consolidation process, old and superseded information is removed, making the topic files smaller and more precise than before the session. This is the mechanism that prevents the knowledge base from growing into noise over time.

The document indicates that autoDream is implemented in the codebase at `src/tasks/DreamTask/` and `src/services/autoDream/`.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer with accurate details and good elaboration, only missing the specific mention of 'Claude Code source' but otherwise comprehensive and correct.

---

### Question 3 — PASS (95/100)

**Question:** Why does Claude Code use 40+ tools with tight domain boundaries instead of fewer general-purpose tools?

**Expected answer (summary):**
Each tool has a single, tight responsibility. A tool that does one thing precisely is more reliable than a tool that tries to do three things loosely. When a tool fails, the agent knows exactly which tool failed and why — because each tool does exactly one thing. This is the tool scoping philosophy from Claude Code's source: tight domain boundaries make failures diagnosable and recoverable.

**Actual answer from LLM:**
According to the document, Claude Code uses 40+ tools with tight domain boundaries because of their tool scoping philosophy: every tool has a single, tight responsibility with a named domain boundary. 

The key reasoning is that "A tool that does one thing precisely is more reliable than a tool that tries to do three things loosely." This approach provides better debugging and error identification because "The agent knows exactly which tool failed and why — because each tool does exactly one thing."

The document gives a concrete example of this principle in practice: "This is directly why the Oracle Forge agent uses separate tools per database type rather than a single 'query database' tool that switches internally."

So the architecture prioritizes reliability and precise error identification over having fewer tools.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer with accurate quotes and even adds a helpful concrete example, demonstrating complete understanding of the tool scoping philosophy.

---

### Question 4 — PASS (95/100)

**Question:** What are session transcripts in Claude Code's memory system and how are they accessed?

**Expected answer (summary):**
Session transcripts are logs of past agent runs. They are never pre-loaded into context — searching is cheap, pre-loading is expensive. The agent searches them only when a new question closely resembles a past one. This is enforced by the context window budget management in QueryEngine.ts.

**Actual answer from LLM:**
Based on the document, session transcripts are Layer 3 of Claude Code's memory architecture. They are logs of past agent runs that contain:

- Which queries were asked
- What tools were called  
- What results came back
- What the final answer was

**How they are accessed:**

Session transcripts are **never pre-loaded into context**. Instead, the agent searches them only when a new question closely resembles a past one. The document gives an example: "This looks like the bookreview query 3 pattern — retrieve the transcript."

The key principle is that **searching is cheap; pre-loading is expensive**. This approach keeps the context window from being bloated with potentially irrelevant historical information.

The source code implementation uses `src/commands/resume` for session restoration from transcripts, and the query pipeline in `src/QueryEngine.ts` manages context window budgets that enforce the never-pre-load discipline.

**Grader reasoning:** The actual answer contains all key concepts from the expected answer with additional accurate detail and no contradictions.

---

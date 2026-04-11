# kb/architecture/ changelog

## 2026-04-11 — Initial KB v1 commit

ADDED: MEMORY.md — context loading index and document registry.
INJECTION TEST: PASS. Question: "In what order does the agent load KB documents at session start?" Answer matched loading order exactly.

ADDED: tool_scoping.md — database-to-tool mapping for all four DAB engine types.
INJECTION TEST: PASS. Question: "A query needs PostgreSQL data and MongoDB data. Which tools do I call?" Answer: query_db for each separately, execute_python to merge. Correct.

ADDED: claude_code_memory.md — three-layer memory architecture from March 2026 Claude Code source leak.
INJECTION TEST: PASS. Question: "What is autoDream and what does it do to topic files?" Answer correctly described background consolidation process.

ADDED: openai_agent_context.md — six-layer context architecture from OpenAI January 2026 data agent writeup.
INJECTION TEST: PASS. Question: "What is Layer 5 and what is the Oracle Forge equivalent?" Answer correctly identified learning memory and corrections log.

ADDED: kb_v1_architecture.md — KB structure rules and Karpathy method discipline.
INJECTION TEST: PASS. Question: "What are the four KB subdirectories and what does each contain?" Answer matched all four subdirectory descriptions.

ADDED: CHANGELOG.md (this file).

## 2026-04-11 — Injection test failure fixes (round 3)

UPDATED: tool_scoping.md — "Do not return zero-row result to user" added as explicit standalone first line before numbered sequence. Duplicate cross-database steps removed from zero-rows section.
INJECTION TEST: re-run required.

UPDATED: openai_agent_context.md — Self-correction section now opens with "The agent evaluates its own intermediate results during execution — not only at the end." Core problem section restructured: DAB join key mismatch and domain-specific business terms now stated as explicit standalone sentences in their own paragraph.
INJECTION TEST: re-run required.

UPDATED: claude_code_memory.md — autoDream source paths moved to opening sentence. Layer 3 session transcripts restructured: QueryEngine.ts enforcement now in first sentence of section, not buried in source note.
INJECTION TEST: re-run required.

UPDATED: kb_v1_architecture.md — kb/corrections section now opens with "The file is kb/corrections/log.md" and "written by Drivers after every observed agent failure" in first line. Karpathy section rewritten: all three missing concepts (remove pretraining knowledge, DAB-specific only, sentence-level test) now appear in the first paragraph.
INJECTION TEST: re-run required.

UPDATED: MEMORY.md — tool_scoping.md registry entry now explicitly names all four engine types and includes the sentence "If a question asks why the agent uses separate database tools instead of one general tool, the answer is in tool_scoping.md."
INJECTION TEST: re-run required.
- Update this file every time a document is added, revised, or removed.
- Record the test question and PASS/FAIL result for every change.
- Documents removed must have their removal reason recorded here.
- Do not remove the CHANGELOG.md itself.
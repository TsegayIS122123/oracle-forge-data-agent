# AI-DLC Inception Document — Sprint 1
**Project:** The Oracle Forge — Production Data Analytics Agent  
**Programme:** TRP1 FDE Programme — Tenacious Intelligence Corp  
**Team:** Team Mistral  
**Sprint:** 1 of 2  
**Sprint scope:** Infrastructure · DAB environment · OpenRouter integration · Agent skeleton · Three-layer context architecture · Evaluation harness baseline  
**Prepared by:** Drivers — Nebiyou Belayineh, Hiwot Beyene  
**Date written:** 2026-04-11  
**Status:** DRAFT — awaiting mob session approval  

---

## Team Roster

| Name | Role |
|---|---|
| Nebiyou Belayineh | Driver |
| Hiwot Beyene | Driver |
| Martha Ketsla | Intelligence Officer |
| Nahom Desalegn | Intelligence Officer |
| Tsegaye Assefa | Signal Corps |
| Abdulaziz | Signal Corps |

---

## Section 1 — Press Release

*Written as if this sprint is already complete. Present tense. Specific. Hard to write — that difficulty is the point.*

---

**Team Mistral's Oracle Forge data agent is live on the shared server and answering natural language business questions against two DataAgentBench database types.**

Team Mistral has deployed a working data analytics agent on the team server that accepts plain-English questions and returns verifiable answers with a full query trace. The agent runs against the DataAgentBench benchmark environment — specifically the `bookreview` dataset (PostgreSQL + SQLite) and the `yelp` dataset (DuckDB + MongoDB) — covering all four database engine types required by DAB. The agent implements a three-layer context architecture: Layer 1 loads `tool_scoping.md` before every session, specifying which of the four MCP database tools to call for each engine type; Layer 2 loads the relevant dataset's schema section from `schemas.md` after the question is received; Layer 3 loads the last ten entries of `corrections/log.md` at session start, giving the agent a running record of its own past failures. An evaluation harness traces every tool call, compares agent answers against the DAB ground-truth files, and has produced a first-run baseline pass@1 score recorded in `eval/score_log/run_001_baseline.json`. The DAB agent runs through OpenRouter using the `openai` Python SDK with `base_url="https://openrouter.ai/api/v1"`, added as an `elif` branch in `common_scaffold/DataAgent.py`. The codebase is committed to the team repository, reproducible from a clean clone, and the facilitator can access the live agent via the shared server REST endpoint.

---

## Section 2 — Honest FAQ (User perspective)

*Questions a real user of this agent would ask. Honest answers — including what it does not yet do.*

---

**Q1: I ask the agent a question about the Yelp dataset. Will it give me a correct answer?**

At the end of Sprint 1, the agent handles queries against the `yelp` (DuckDB + MongoDB) and `bookreview` (PostgreSQL + SQLite) datasets. It reads the question, identifies which database to query using its tool scoping knowledge, executes the query through the DAB tools (`query_db`, `list_db`, `execute_python`), and returns a structured answer with a query trace. The answer may not always be correct — the baseline pass@1 score reflects that — but the agent completes the full pipeline from question to answer without crashing. Queries requiring cross-database joins with inconsistently formatted keys (the ill-formatted join key problem) are detected and logged as failures rather than returning a silently wrong answer. Full join key resolution is a Sprint 2 target.

---

**Q2: Can I run the agent from my laptop without installing anything locally?**

Yes. The agent is deployed on the team's shared server. Any team member accesses it by sending a POST request to `http://[server-ip]:8000/query` with a JSON body containing the question and dataset name. No local Python environment or database installation is required. The facilitator can follow the `README.md` in the repository root to verify the agent is running and submit a test question.

---

**Q3: How do I know if the agent's answer is right or wrong?**

Every agent run produces a `final_agent.json` file in `query_[dataset]/query[N]/logs/data_agent/[run_name]/`. This file contains the agent's final answer, the termination reason, and a full trace of every tool call made. The evaluation harness reads these files and compares answers against `ground_truth.csv` using each query's `validate.py`. The harness outputs a score to `eval/score_log/`. A result of `"is_valid": true` means the agent matched the ground truth. A result of `"is_valid": false` includes the reason it failed and both the agent answer and the ground truth — this is what feeds the corrections log.

---

## Section 3 — Honest FAQ (Technical perspective)

*What could go wrong. What the hardest part is. What dependencies exist. No optimism.*

---

**Q1: What is the highest-risk assumption in this sprint?**

The highest-risk assumption is that OpenRouter's tool-calling API behaves identically to the OpenAI API for the models we select. The DAB agent's `call_llm()` method relies on `response.choices[0].message.tool_calls` — if the chosen OpenRouter model returns tool calls in a different format, the agent will silently fail with `terminate_reason: no_tool_call` and return the raw LLM content as the answer instead of executing database queries. Mitigation: on Day 2, Drivers run a single smoke-test query against `bookreview` query 1 using `--iterations 5` and inspect `llm_calls.jsonl` to confirm `tool_calls` is populated in the response. If it is not, we switch to a model with confirmed tool-calling support on OpenRouter (e.g., `anthropic/claude-3.5-sonnet` or `openai/gpt-4o-mini`) before proceeding.

---

**Q2: What dependency could block the evaluation harness from producing a meaningful score?**

The harness requires three things to exist simultaneously: a running agent that produces `final_agent.json` files, a held-out test set with expected answers defined, and the DAB `validate.py` scripts which are already in the repository per dataset. The dependency is the agent producing any output at all. If the agent crashes on every query, the harness has nothing to score. If this happens, the harness is run against the DAB-provided example output structure (from the README) to verify the harness itself works, and the score log is populated with `pass@1 = 0.0` as the true baseline. An honest zero is still a baseline — it proves the harness runs.

---

**Q3: What is the most likely cause of missing the interim deadline (April 15)?**

Git LFS files not downloading correctly. The DAB repository stores large database files (`.db`, `.duckdb`, `.sql`) in Git LFS. If `git lfs install` is not run before `git clone`, all database files arrive as pointer text files of a few hundred bytes. The agent will then fail every query with a database connection or file-not-found error. This is invisible unless you explicitly run `ls -lh query_yelp/query_dataset/` and check that files show megabyte sizes. Mitigation: Day 1 infrastructure verification includes this exact check as a gated step before any further work proceeds. If LFS files are wrong, `git lfs pull` is run immediately and verified before moving forward.

---

## Section 4 — Key Decisions

*Each decision with the chosen option and a one-sentence reason. No decision by default.*

---

**Decision 1: LLM provider**  
Chosen: OpenRouter, integrated via the `openai` Python SDK with `base_url="https://openrouter.ai/api/v1"` and an `OPENROUTER_API_KEY` environment variable.  
Reason: The team does not have access to Azure, Gemini, or Together.AI API keys; OpenRouter provides a single unified endpoint covering hundreds of models through the standard OpenAI SDK interface, requiring only a two-line change to `DataAgent.py`.

---

**Decision 2: Starting model on OpenRouter**  
Chosen: `anthropic/claude-3.5-sonnet` for smoke testing and first baseline run; `meta-llama/llama-3.1-8b-instruct:free` as the fallback if credits are limited.  
Reason: Claude 3.5 Sonnet has confirmed tool-calling support on OpenRouter and appears on the DAB leaderboard (`Claude-Opus-4.6` scored 43.76%), giving us confidence the model family handles the DAB tool-call protocol correctly.

---

**Decision 3: Starting datasets**  
Chosen: `bookreview` (PostgreSQL + SQLite) first, `yelp` (DuckDB + MongoDB) second.  
Reason: `bookreview` has the simplest schema (2 tables, 2 databases) and is the DAB README's own example command, making it the lowest-risk starting point for verifying the full pipeline; `yelp` adds DuckDB and MongoDB coverage, completing all four engine types within Sprint 1.

---

**Decision 4: Agent access method**  
Chosen: REST API endpoint deployed on the shared server at `http://[server-ip]:8000/query`, wrapping `run_agent.py` via a FastAPI server built in Sprint 1 Construction.  
Reason: tenai-infra was successfully run once but the team encountered blockers on subsequent attempts; a simple FastAPI wrapper provides facilitator-accessible agent access without requiring Tailscale or tmux knowledge from non-Driver team members, while tenai is revisited in Sprint 2.

---

**Decision 5: Context loading implementation**  
Chosen: A dedicated `agent/context_loader.py` module that implements the six-layer loading order, called at agent session start before any question is processed.  
Reason: Separating context loading into its own module makes it independently testable — Intelligence Officers can run injection tests on KB documents without needing a running database connection.

---

**Decision 6: Sandbox environment**  
Chosen: DAB's built-in Docker sandbox (`python-data:3.12` image built from the DAB `Dockerfile`), invoked by the existing `ExecTool` in `common_scaffold/tools/ExecTool.py`.  
Reason: The sandbox is already implemented in the DAB scaffold and requires only `docker build -t python-data:3.12 .` to activate — building a separate sandbox wastes Sprint 1 time that should go to context engineering.

---

## Section 5 — Definition of Done

*Numbered, specific, verifiable. Each item states exactly what evidence proves it is done — not "I think it works" but "here is the file that proves it works."*

---

**1. DataAgentBench repository cloned with real Git LFS database files.**  
Evidence: Running `ls -lh DataAgentBench/query_yelp/query_dataset/` shows files with sizes in megabytes (not hundreds of bytes). Screenshot saved to `planning/evidence/01_lfs_verify.png`.

**2. DAB Conda environment created and all dependencies installed.**  
Evidence: Running `conda activate dabench && python -c "import duckdb, pymongo, psycopg2, openai; print('OK')"` prints `OK` with no import errors. Output saved to `planning/evidence/02_env_verify.txt`.

**3. Docker sandbox image built and functional.**  
Evidence: Running `docker images | grep python-data` shows `python-data:3.12` in the image list. Running `docker run --rm python-data:3.12 python -c "import pandas, pyarrow; print('OK')"` prints `OK`. Output saved to `planning/evidence/03_docker_verify.txt`.

**4. PostgreSQL 17 running and accessible with correct credentials.**  
Evidence: Running `psql -U postgres -h 127.0.0.1 -c "\l"` lists available databases without error. Output saved to `planning/evidence/04_postgres_verify.txt`.

**5. MongoDB running and accessible.**  
Evidence: Running `mongosh --eval "db.runCommand({ping:1})"` returns `{ ok: 1 }`. Output saved to `planning/evidence/05_mongo_verify.txt`.

**6. OpenRouter integration added to `common_scaffold/DataAgent.py` and smoke test passes.**  
Evidence: Running `python run_agent.py --dataset bookreview --query_id 1 --llm anthropic/claude-3.5-sonnet --iterations 10 --root_name smoke_0` completes without a Python exception. The file `query_bookreview/query1/logs/data_agent/smoke_0/final_agent.json` exists and contains a non-empty `"final_result"` field and a `"terminate_reason"` that is either `"return_answer"` or `"max_iterations"` — not an error string. File path saved to `planning/evidence/06_smoke_test.txt`.

**7. Agent skeleton deployed on shared server with REST endpoint responding.**  
Evidence: Running `curl -X POST http://[server-ip]:8000/query -H "Content-Type: application/json" -d '{"dataset":"bookreview","query_id":1}'` returns a JSON response containing `"answer"` and `"trace"` fields within 60 seconds. Response saved to `planning/evidence/07_server_verify.json`.

**8. Three context layers implemented in `agent/context_loader.py` and loading in correct order.**  
Evidence: Running the agent with `--debug-context` flag (or reading the `llm_calls.jsonl` first entry) shows the system prompt contains content from `tool_scoping.md`, `corrections/log.md` (or the message "corrections log not yet created"), and `MEMORY.md`, in that order, before the user question appears. Log excerpt saved to `planning/evidence/08_context_layer_trace.txt`.

**9. KB v1 (architecture) committed with two documents passing injection tests.**  
Evidence: `kb/architecture/tool_scoping.md` and `kb/architecture/MEMORY.md` exist. `kb/architecture/injection_tests/tool_scoping_test.md` and `kb/architecture/injection_tests/MEMORY_test.md` each contain the test question, the expected answer, and the word "PASS". Intelligence Officers confirm at mob session that both tests were run on fresh LLM sessions with only the document as context.

**10. KB v2 (domain) committed with `schemas.md` for `bookreview` and `yelp` datasets passing injection tests.**  
Evidence: `kb/domain/schemas.md` contains sections for both datasets documenting table names, column names, data types, and database engine. `kb/domain/injection_tests/schemas_test.md` exists with "PASS" result. The test question used: *"What tables exist in the bookreview dataset, what columns do they have, and which database engine stores each table?"*

**11. Evaluation harness producing a first-run baseline score.**  
Evidence: Running `python eval/harness.py --dataset bookreview --runs smoke_0` (or equivalent harness command) completes and writes `eval/score_log/run_001_baseline.json`. The file contains at minimum: `dataset`, `pass_at_1`, `total_queries_run`, `timestamp`, and `per_query_results`. The numeric value of `pass_at_1` does not matter — its existence and structure is the check. File saved and committed to `eval/score_log/`.

**12. At least three shared utility modules committed with passing tests.**  
Evidence: `utils/` directory contains `multi_pass_retrieval.py`, `schema_introspector.py`, and `join_key_resolver.py` (or equivalent). Running `python -m pytest utils/tests/ -v` passes all tests with zero failures. Output saved to `planning/evidence/12_utils_tests.txt`.

**13. Sprint 1 Inception document approved by full team at mob session.**  
Evidence: `planning/sprint_01_mob_approval.md` exists and contains: the date of the approval mob session, the names of all six team members present, the hardest question asked about this document, and the answer the team agreed on. No Construction code was committed before this file was created.

**14. `README.md` at repository root is complete and setup is reproducible.**  
Evidence: A team member who was not involved in server setup can follow only the `README.md` and reach a working agent endpoint. Verified live at the interim mob session as a demonstration. The README contains: team roster with roles, architecture diagram (hand-drawn photograph acceptable), setup commands in order, and the server URL.

---

## Section 6 — Sprint 1 Scope Boundary

*Explicit list of what is NOT in this sprint, to prevent scope creep during Construction.*

The following are deliberately deferred to Sprint 2. They must not be built during Sprint 1 Construction even if they appear easy:

- Full silent self-correction loop for failed queries (Sprint 2 target)
- Join key resolver for cross-database entity ID format mismatches (Sprint 2)
- Unstructured text extraction pipeline — `text_extractor.py` (Sprint 2)
- MongoDB and DuckDB adversarial probes (Sprint 2 — probes are built after baseline)
- Full DAB benchmark run — 54 queries × 50 trials (Sprint 2, Week 9 Days 3–4)
- KB v3 corrections log population (the file is created in Sprint 1; entries are added during Sprint 2 as the agent runs and fails)
- All datasets beyond `bookreview` and `yelp` (Sprint 2 target, after baseline established)
- LinkedIn/Medium articles (Signal Corps Sprint 2 deliverable)

---

## Section 7 — Sprint 1 Timeline

| Day | Primary focus | Owner | Gate |
|---|---|---|---|
| Day 1 (Apr 11) | Inception document written and approved. System installations: git-lfs, PostgreSQL 17, MongoDB, Docker, Conda. DAB repo cloned with LFS files verified. Raw KB domain files extracted from DAB and handed to Intelligence Officers. | Drivers + full team mob | Inception approval recorded in `sprint_01_mob_approval.md` |
| Day 2 (Apr 12) | OpenRouter branch added to `DataAgent.py`. Smoke test on `bookreview` query 1. Docker image built. `.env` configured. Agent skeleton construction begins. | Drivers | Smoke test produces non-empty `final_agent.json` |
| Day 3 (Apr 13) | Agent skeleton with context loader complete. `bookreview` and `yelp` datasets loading. REST endpoint deployed on shared server. KB v1 injection tests complete. | Drivers + Intelligence Officers | Server endpoint responding to curl |
| Day 4 (Apr 14) | Evaluation harness baseline run complete. KB v2 committed with injection tests. Three utility modules committed. README draft complete. | All roles | `run_001_baseline.json` exists |
| Day 5 (Apr 15) | All evidence files saved and committed. Final README verified end-to-end. Interim submission packaged: GitHub repo + PDF report. **Interim deadline: 21:00 UTC** | All roles | Submission sent |

---

## Section 8 — DAB Dataset Reference for Sprint 1

*Sourced from the DataAgentBench repository. This is what the agent will be evaluated against.*

| Dataset | DB engines | Tables | Queries | Sprint target |
|---|---|---|---|---|
| `bookreview` | PostgreSQL + SQLite | 2 | 3 | Primary — all 3 queries attempted |
| `yelp` | DuckDB + MongoDB | 5 | 7 | Secondary — all 7 queries attempted |
| All others | Various | Various | 44 | Sprint 2 |

**Why these two datasets first:** `bookreview` is the DAB README's own example command and has the simplest schema (2 tables). `yelp` is explicitly identified by the Practitioner Manual as "the recommended starting point" because it "contains multi-source data, nested JSON, missing values, and entity resolution challenges that mirror the full DAB problem space in a contained form." Together these two datasets cover all four database engines: PostgreSQL, SQLite, DuckDB, MongoDB.

**DAB tool reference (already implemented in `common_scaffold/tools/`):**

| Tool name | What it does | Used for |
|---|---|---|
| `query_db` | Executes read-only queries against any configured DB | PostgreSQL, SQLite, DuckDB, MongoDB queries |
| `list_db` | Lists available databases and their tables | Schema discovery at session start |
| `execute_python` | Runs Python code in Docker sandbox with 600s timeout | Data transformation, joining results across DBs |
| `return_answer` | Terminates the agent loop and records the final answer | Final answer submission |

---

## Approval Record

*To be completed at the mob session where this document is read and approved. No Construction begins before this section is filled in.*

| Field | Value |
|---|---|
| Mob session date | April 11 , 2026 |
| Team members present | _______________ |
| Hardest question asked | _______________ |
| Answer agreed by team | _______________ |
| Approved to proceed to Construction | YES / NO |
| Recorded by | _______________ |


---

*Document version: 1.0 — initial draft by Drivers (Nebiyou Belayineh, Hiwot Beyene)*  
*Next review: Construction gate — mob session at end of Sprint 1 Construction phase*  
*Programme: TRP1 FDE Programme · Tenacious Intelligence Corp · April 2026*
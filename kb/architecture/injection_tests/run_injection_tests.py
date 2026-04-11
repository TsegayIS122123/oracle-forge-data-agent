"""
Oracle Forge — KB Architecture Injection Test Runner
=====================================================
Runs injection tests for all kb/architecture/ documents using OpenRouter.
Results are written back into the corresponding test .md files.

Usage:
    python3 run_injection_tests.py                     # run all tests
    python3 run_injection_tests.py --doc tool_scoping  # run one document
    python3 run_injection_tests.py --doc claude_code_memory

Requirements:
    pip3 install openai python-dotenv

Environment:
    OPENROUTER_API_KEY in repo-root .env, DataAgentBench/.env, or exported.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import UTC, datetime
from openai import OpenAI
from dotenv import load_dotenv

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
KB_ARCH_DIR  = SCRIPT_DIR.parent          # kb/architecture/
REPO_ROOT    = KB_ARCH_DIR.parent.parent  # project root
ENV_FILE     = REPO_ROOT / "DataAgentBench" / ".env"
REPO_ENV     = REPO_ROOT / ".env"

for candidate in [ENV_FILE, REPO_ENV, Path("/DataAgentBench/.env"), Path(".env")]:
    if candidate.exists():
        load_dotenv(candidate)
        break

# ── OpenRouter client ───────────────────────────────────────────────────────
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    sys.exit(
        "ERROR: OPENROUTER_API_KEY not set.\n"
        "Add it to your .env file or export it:\n"
        "  export OPENROUTER_API_KEY=sk-or-v1-..."
    )

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/team-mistral/oracle-forge",
        "X-Title": "Oracle Forge KB Injection Tests",
    },
)

MODEL = os.getenv("INJECTION_TEST_MODEL", "anthropic/claude-3.7-sonnet")

# ── document registry ───────────────────────────────────────────────────────
# Maps --doc argument → (kb document file, test file)
DOCUMENTS = {
    "MEMORY": {
        "doc_file": KB_ARCH_DIR / "MEMORY.md",
        "test_file": SCRIPT_DIR / "MEMORY_test.md",
        "priority": 1,  # tested first — most critical, loaded every session
    },
    "tool_scoping": {
        "doc_file": KB_ARCH_DIR / "tool_scoping.md",
        "test_file": SCRIPT_DIR / "tool_scoping_test.md",
        "priority": 2,  # mandatory, loaded before every question
    },
    "claude_code_memory": {
        "doc_file": KB_ARCH_DIR / "claude_code_memory.md",
        "test_file": SCRIPT_DIR / "claude_code_memory_test.md",
        "priority": 3,
    },
    "openai_agent_context": {
        "doc_file": KB_ARCH_DIR / "openai_agent_context.md",
        "test_file": SCRIPT_DIR / "openai_agent_context_test.md",
        "priority": 4,
    },
    "kb_v1_architecture": {
        "doc_file": KB_ARCH_DIR / "kb_v1_architecture.md",
        "test_file": SCRIPT_DIR / "kb_v1_architecture_test.md",
        "priority": 5,
    },
}


def load_document(path: Path) -> str:
    """Read a KB document. Abort clearly if it does not exist."""
    if not path.exists():
        sys.exit(f"ERROR: Document not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def extract_qa_pairs(test_content: str) -> list[dict]:
    """
    Parse test file to extract question/expected-answer pairs.
    Looks for blocks:
        ### Question N
        "<question text>"

        Expected answer:
        <answer text>
    """
    pairs = []
    blocks = re.split(r"### Question \d+", test_content)
    for block in blocks[1:]:  # skip preamble before first question
        q_match = re.search(r'"(.+?)"', block, re.DOTALL)
        a_match = re.search(r"Expected answer:\s*\n(.+?)(?=\n###|\n---|\Z)", block, re.DOTALL)
        if q_match and a_match:
            pairs.append({
                "question": q_match.group(1).strip(),
                "expected": a_match.group(1).strip(),
            })
    return pairs


def call_openrouter(document_text: str, question: str) -> str:
    """
    Send a single injection test call to OpenRouter.
    The document is the ONLY context — no system prompt, no other knowledge.
    """
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=600,
        messages=[
            {
                "role": "user",
                "content": (
                    f"The following is the only document you have access to. "
                    f"Answer the question using only the information in this document. "
                    f"Do not use any other knowledge.\n\n"
                    f"DOCUMENT:\n{document_text}\n\n"
                    f"QUESTION:\n{question}"
                ),
            }
        ],
    )
    return response.choices[0].message.content.strip()


def grade_answer(question: str, expected: str, actual: str) -> dict:
    """
    Use OpenRouter to grade whether the actual answer matches the expected answer.
    Returns {"pass": bool, "score": 0-100, "reasoning": str}
    """
    grader_prompt = (
        f"You are a strict grader for an AI agent knowledge base injection test.\n\n"
        f"QUESTION: {question}\n\n"
        f"EXPECTED ANSWER:\n{expected}\n\n"
        f"ACTUAL ANSWER:\n{actual}\n\n"
        f"Grade the actual answer. It PASSES if it contains the key concepts from the expected answer "
        f"without contradicting them. Minor wording differences are acceptable. "
        f"Missing key concepts is a FAIL. Wrong information is a FAIL.\n\n"
        f"Respond with JSON only, no other text:\n"
        f'{{"pass": true/false, "score": 0-100, "reasoning": "one sentence"}}'
    )
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": grader_prompt}],
    )
    raw = response.choices[0].message.content.strip()
    # strip markdown fences if present
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"pass": False, "score": 0, "reasoning": f"Grader returned unparseable output: {raw}"}


def write_results_to_test_file(test_file: Path, results: list[dict], doc_name: str) -> None:
    """
    Write test results into the ## Test result section of the test file.
    Replaces everything from '## Test result' to end of file.
    """
    content = test_file.read_text(encoding="utf-8")

    # strip everything from ## Test result onward
    marker = "## Test result"
    if marker in content:
        content = content[: content.index(marker)].rstrip()

    # build result block
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    overall_pass = all(r["grade"]["pass"] for r in results)
    avg_score = round(sum(r["grade"]["score"] for r in results) / len(results), 1)

    lines = [
        "",
        "## Test result",
        "",
        f"**Run timestamp:** {timestamp}",
        f"**Model used:** {MODEL}",
        f"**Document tested:** kb/architecture/{doc_name}.md",
        f"**Overall result:** {'PASS' if overall_pass else 'FAIL'}",
        f"**Average score:** {avg_score}/100",
        "",
    ]

    for i, r in enumerate(results, start=1):
        grade = r["grade"]
        status = "PASS" if grade["pass"] else "FAIL"
        lines += [
            f"### Question {i} — {status} ({grade['score']}/100)",
            "",
            f"**Question:** {r['question']}",
            "",
            f"**Expected answer (summary):**",
            r["expected"],
            "",
            f"**Actual answer from LLM:**",
            r["actual"],
            "",
            f"**Grader reasoning:** {grade['reasoning']}",
            "",
            "---",
            "",
        ]

    updated = content + "\n" + "\n".join(lines)
    test_file.write_text(updated, encoding="utf-8")
    print(f"  Results written to {test_file.name}")


def run_test_for_document(doc_key: str) -> bool:
    """Run all injection tests for one document. Returns True if all passed."""
    entry = DOCUMENTS[doc_key]
    doc_file  = entry["doc_file"]
    test_file = entry["test_file"]

    print(f"\n{'='*60}")
    print(f"Testing: {doc_key}")
    print(f"  Document : {doc_file}")
    print(f"  Test file: {test_file}")

    if not test_file.exists():
        print(f"  SKIP: test file not found at {test_file}")
        return True

    document_text = load_document(doc_file)
    test_content  = test_file.read_text(encoding="utf-8")
    qa_pairs      = extract_qa_pairs(test_content)

    if not qa_pairs:
        print(f"  SKIP: no Q&A pairs found in test file")
        return True

    print(f"  Found {len(qa_pairs)} test question(s). Running...")

    results = []
    for i, pair in enumerate(qa_pairs, start=1):
        print(f"  Q{i}: {pair['question'][:80]}...")
        actual = call_openrouter(document_text, pair["question"])
        grade  = grade_answer(pair["question"], pair["expected"], actual)
        status = "PASS" if grade["pass"] else "FAIL"
        print(f"       → {status} ({grade['score']}/100) — {grade['reasoning']}")
        results.append({
            "question": pair["question"],
            "expected": pair["expected"],
            "actual":   actual,
            "grade":    grade,
        })

    write_results_to_test_file(test_file, results, doc_key)
    all_passed = all(r["grade"]["pass"] for r in results)
    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Oracle Forge KB injection test runner"
    )
    parser.add_argument(
        "--doc",
        choices=list(DOCUMENTS.keys()),
        default=None,
        help="Test a single document. Omit to test all documents.",
    )
    args = parser.parse_args()

    print(f"Oracle Forge — KB Injection Test Runner")
    print(f"Model: {MODEL}")
    print(f"Timestamp: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")

    if args.doc:
        targets = [args.doc]
    else:
        # Run in priority order — most critical documents first
        targets = sorted(DOCUMENTS.keys(), key=lambda k: DOCUMENTS[k]["priority"])

    passed = []
    failed = []
    for doc_key in targets:
        ok = run_test_for_document(doc_key)
        (passed if ok else failed).append(doc_key)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Passed : {len(passed)} — {passed}")
    print(f"  Failed : {len(failed)} — {failed}")

    if failed:
        print("\nFAILED documents must be revised before committing.")
        print("Re-run after revision:")
        for f in failed:
            print(f"  python3 run_injection_tests.py --doc {f}")
        sys.exit(1)
    else:
        print("\nAll injection tests PASSED. Documents are safe to commit.")


if __name__ == "__main__":
    main()
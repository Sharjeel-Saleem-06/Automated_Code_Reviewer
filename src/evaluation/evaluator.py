"""
Evaluation framework for agent output quality.

Tests the multi-agent system against known-vulnerable code samples
and verifies agents detect the expected issues.

JD Coverage:
- "Develop testing and evaluation frameworks to minimize hallucinations"
- "Monitor agent performance and iterate based on feedback and metrics"
"""
import json
import time
from dataclasses import dataclass, field


@dataclass
class TestCase:
    name: str
    diff: str
    expected_security: list[str]  # expected vulnerability types
    expected_logic: list[str]     # expected bug types
    expected_performance: list[str]  # expected perf issues


@dataclass
class EvalResult:
    test_name: str
    agent: str
    expected_count: int
    found_count: int
    expected_types: list[str]
    found_types: list[str]
    true_positives: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)
    precision: float = 0.0
    recall: float = 0.0


SQL_INJECTION_DIFF = """diff --git a/app.py b/app.py
+import sqlite3
+def get_user(username):
+    conn = sqlite3.connect('db.sqlite')
+    cursor = conn.execute(f"SELECT * FROM users WHERE name = '{username}'")
+    return cursor.fetchone()"""

HARDCODED_SECRET_DIFF = """diff --git a/config.py b/config.py
+API_KEY = "sk-live-abc123xyz789"
+DB_PASSWORD = "supersecret123"
+def connect():
+    return create_engine(f"postgresql://admin:{DB_PASSWORD}@localhost/prod")"""

N_PLUS_ONE_DIFF = """diff --git a/api.py b/api.py
+def get_users_with_posts():
+    users = db.query("SELECT * FROM users").fetchall()
+    for user in users:
+        posts = db.query(f"SELECT * FROM posts WHERE user_id = {user['id']}").fetchall()
+        user['posts'] = posts
+    return users"""

CLEAN_DIFF = """diff --git a/utils.py b/utils.py
+def add(a: int, b: int) -> int:
+    return a + b
+
+def safe_divide(a: float, b: float) -> float:
+    if b == 0:
+        return 0.0
+    return a / b"""


TEST_SUITE = [
    TestCase(
        name="SQL Injection Detection",
        diff=SQL_INJECTION_DIFF,
        expected_security=["SQL Injection"],
        expected_logic=[],
        expected_performance=[],
    ),
    TestCase(
        name="Hardcoded Secrets Detection",
        diff=HARDCODED_SECRET_DIFF,
        expected_security=["Hardcoded Secret"],
        expected_logic=[],
        expected_performance=[],
    ),
    TestCase(
        name="N+1 Query Detection",
        diff=N_PLUS_ONE_DIFF,
        expected_security=["SQL Injection"],
        expected_logic=[],
        expected_performance=["N+1 Query"],
    ),
    TestCase(
        name="Clean Code (No False Positives)",
        diff=CLEAN_DIFF,
        expected_security=[],
        expected_logic=[],
        expected_performance=[],
    ),
]


def evaluate_agent_output(test_case: TestCase, agent_name: str, result: dict) -> EvalResult:
    """Evaluate a single agent's output against expected findings."""
    if agent_name == "security":
        expected = test_case.expected_security
    elif agent_name == "logic":
        expected = test_case.expected_logic
    elif agent_name == "performance":
        expected = test_case.expected_performance
    else:
        expected = []

    findings = result.get("findings", [])
    found_types = []
    for f in findings:
        vtype = f.get("vulnerability_type") or f.get("bug_type") or f.get("issue_type", "unknown")
        found_types.append(vtype)

    expected_lower = [e.lower() for e in expected]
    found_lower = [f.lower() for f in found_types]

    true_positives = []
    missed = []
    for exp in expected_lower:
        if any(exp in found for found in found_lower):
            true_positives.append(exp)
        else:
            missed.append(exp)

    recall = len(true_positives) / len(expected_lower) if expected_lower else 1.0

    if found_lower:
        tp_count = sum(1 for f in found_lower if any(e in f for e in expected_lower))
        precision = tp_count / len(found_lower) if found_lower else 0.0
    else:
        precision = 1.0 if not expected_lower else 0.0

    return EvalResult(
        test_name=test_case.name,
        agent=agent_name,
        expected_count=len(expected),
        found_count=len(findings),
        expected_types=expected,
        found_types=found_types,
        true_positives=true_positives,
        missed=missed,
        precision=precision,
        recall=recall,
    )


def run_evaluation(run_agent_fn) -> list[EvalResult]:
    """Run the full evaluation suite. run_agent_fn(diff) should return agent results dict."""
    results = []
    for tc in TEST_SUITE:
        print(f"\n  Eval: {tc.name}")
        agent_result = run_agent_fn(tc.diff)

        for review in agent_result.get("reviews", []):
            agent_name = review.get("agent", "unknown")
            eval_result = evaluate_agent_output(tc, agent_name, review)
            results.append(eval_result)
            status = "PASS" if eval_result.recall >= 0.8 else "FAIL"
            print(f"    [{status}] {agent_name}: recall={eval_result.recall:.0%}, precision={eval_result.precision:.0%}")

    return results


def print_eval_summary(results: list[EvalResult]):
    """Pretty-print evaluation summary."""
    total = len(results)
    passing = sum(1 for r in results if r.recall >= 0.8)
    avg_recall = sum(r.recall for r in results) / total if total else 0
    avg_precision = sum(r.precision for r in results) / total if total else 0

    print("\n" + "=" * 50)
    print("  EVALUATION SUMMARY")
    print("=" * 50)
    print(f"  Tests Run    : {total}")
    print(f"  Passing      : {passing}/{total}")
    print(f"  Avg Recall   : {avg_recall:.0%}")
    print(f"  Avg Precision: {avg_precision:.0%}")
    print("=" * 50)

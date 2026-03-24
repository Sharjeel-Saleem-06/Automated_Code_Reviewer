# pyre-ignore-all-errors
"""
╔══════════════════════════════════════════════════════════════════╗
║     PHASE 1 — LESSON 4: Structured Output (JSON Responses)      ║
╚══════════════════════════════════════════════════════════════════╝

GOAL: Force Claude to ALWAYS reply in strict JSON format.
      This is the bridge between "chatbot" and "automation system".

WHAT YOU'LL LEARN:
  ✅ Why automation systems NEED structured JSON (not free text)
  ✅ How to instruct Claude to output valid JSON
  ✅ How to parse and use Claude's JSON output in your code
  ✅ How to validate the output & handle errors gracefully

JD CONNECTION:
  The JD says: "Implement structured outputs (JSON schemas),
  tool calling, and function execution pipelines."
  JSON output is Step 1 of that pipeline.

HOW TO RUN:
  python Phase1_Hello_Claude/lesson4_structured_output.py
"""

import os
import json
from dotenv import load_dotenv  # type: ignore
import anthropic 

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("=" * 60)
print("  LESSON 4: Structured JSON Output")
print("=" * 60)


# ── WHY JSON? The Free Text Problem ──────────────────────────────
print("\n📌 THE PROBLEM: Claude's free text is useless for automation")
print("─" * 40)
print("  Imagine Claude returns this:")
print('  "There are two issues: first, there\'s a SQL injection')
print('   problem on line 12. Second, the password is hardcoded."')
print()
print("  Now try to programmatically:")
print("  - Count the exact number of issues ❌")
print("  - Get just the file name        ❌")
print("  - Auto-create a GitHub comment  ❌")
print("  It's impossible with free text!")
print()
print("  But if Claude returns JSON, you can do all of this easily ✅")


# ── SOLUTION: Define a strict JSON schema in the system prompt ────

SYSTEM_PROMPT = """You are a code security reviewer.

When given a code snippet, analyze it for security vulnerabilities.

You MUST respond with ONLY valid JSON in this exact structure — no other text:
{
  "review_passed": true or false,
  "total_issues": <number>,
  "severity_level": "critical" | "high" | "medium" | "low" | "none",
  "issues": [
    {
      "id": 1,
      "vulnerability": "<name of vulnerability>",
      "line_hint": "<approximate line>",
      "description": "<what the problem is>",
      "fix": "<the corrected code>"
    }
  ],
  "summary": "<one sentence summary for a PR comment>"
}

If there are NO issues, return an empty issues array and set review_passed to true."""


# ── Test it with real buggy code ──────────────────────────────────
BUGGY_CODE = """
def authenticate(username, password):
    SECRET_KEY = "my_super_secret_123"
    
    conn = sqlite3.connect("users.db")
    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    result = conn.execute(query)
    return result.fetchone() is not None
"""

print("\n\n📌 SENDING BUGGY CODE TO CLAUDE...")
print("─" * 40)
print("Code being reviewed:")
print(BUGGY_CODE)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=SYSTEM_PROMPT,
    messages=[
        {
            "role": "user",
            "content": f"Review this Python code:\n\n```python{BUGGY_CODE}```"
        }
    ]
)

raw_text = response.content[0].text

print("\n📨 Claude's raw response:")
print(raw_text)


# ── Parse the JSON — this is what makes it USABLE ────────────────
print("\n\n📌 PARSING THE JSON — Now we can USE the data in code")
print("─" * 40)

try:
    result = json.loads(raw_text)
    
    # Now we can access structured data programmatically!
    print(f"  ✅ JSON parsed successfully")
    print(f"  Review passed?  : {'✅ PASS' if result['review_passed'] else '❌ FAIL'}")
    print(f"  Total issues    : {result['total_issues']}")
    print(f"  Severity level  : {result['severity_level'].upper()}")
    print(f"  Summary         : {result['summary']}")
    print(f"\n  Issues found:")
    for issue in result["issues"]:
        print(f"    [{issue['id']}] {issue['vulnerability']}")
        print(f"         Line: {issue['line_hint']}")
        print(f"         Fix : {issue['fix'][:70]}...")
    
    # In production, this data would be used to:
    # - Automatically block the PR if severity is "critical"
    # - Post a formatted comment to GitHub
    # - Log findings to a database
    # - Trigger a Slack notification
    print("\n💡 KEY INSIGHT:")
    print("  This structured data can now drive AUTOMATIC decisions:")
    if result["severity_level"] == "critical":
        print("  🚨 Severity is CRITICAL → Block PR merge automatically")
    print("  → Post formatted comment to GitHub PR  ✅")
    print("  → Log to database                      ✅")
    print("  → Send Slack alert                     ✅")
    print("\n  This is exactly what 'function execution pipelines' means in the JD.")

except json.JSONDecodeError as e:
    print(f"  ❌ Failed to parse JSON: {e}")
    print("  This is why we need STRONG system prompts + validation.")
    print("  In Phase 7, we'll add DeepEval to catch these failures.")

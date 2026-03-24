# pyre-ignore-all-errors
"""
╔══════════════════════════════════════════════════════════════════╗
║          PHASE 1 — LESSON 2: System Prompts & Roles             ║
╚══════════════════════════════════════════════════════════════════╝

GOAL: Give Claude a "personality" using a System Prompt.
      Make it act as a Code Review Expert specifically.

WHAT YOU'LL LEARN:
  ✅ What a System Prompt is and why it's powerful
  ✅ How to use "role" to set Claude's personality
  ✅ The difference between system prompt vs user message
  ✅ Why Claude is very different depending on its system prompt

JD CONNECTION:
  The JD says: "Create and optimize advanced prompt engineering
  frameworks." System prompts are Step 1 of that.

HOW TO RUN:
  python Phase1_Hello_Claude/lesson2_system_prompts.py
"""

import os
from dotenv import load_dotenv  # type: ignore
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── EXPERIMENT: Same question, VERY different system prompts ──────

QUESTION = "What should I check when reviewing this Python function?\n\ndef divide(a, b):\n    return a / b"

print("=" * 60)
print("  LESSON 2: Power of System Prompts")
print("=" * 60)


# ── Test 1: No system prompt (Claude is a general assistant) ──────
print("\n📌 TEST 1: No system prompt (generic assistant)")
print("─" * 40)

response1 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=300,
    # No 'system' parameter here
    messages=[{"role": "user", "content": QUESTION}]
)
print(response1.content[0].text)


# ── Test 2: System prompt as a casual Python tutor ────────────────
print("\n\n📌 TEST 2: System prompt — Python Tutor")
print("─" * 40)

response2 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=300,
    system="You are a friendly Python tutor teaching beginners. "
           "Use simple language and encouraging tone.",
    messages=[{"role": "user", "content": QUESTION}]
)
print(response2.content[0].text)


# ── Test 3: System prompt as a STRICT production code reviewer ────
# Notice: This is closer to what our real agents will use
print("\n\n📌 TEST 3: System prompt — Senior Code Reviewer (our target)")
print("─" * 40)

response3 = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=600,
    system="""You are a Senior Software Engineer conducting a production code review.
Your job is to identify ONLY real bugs and security issues — not style preferences.
Be specific, direct, and cite the exact line. Format your response as a numbered list.""",
    messages=[{"role": "user", "content": QUESTION}]
)
print(response3.content[0].text)


print("\n\n" + "─" * 60)
print("💡 KEY INSIGHT:")
print("  The SAME question → 3 completely different responses.")
print("  The SYSTEM PROMPT is the most powerful tool you have.")
print("")
print("  In our code review project:")
print("  - Agent 1 (Logic Bugs) will have a 'software engineer' system prompt")
print("  - Agent 2 (Security) will have a 'security expert' system prompt")
print("  - Agent 3 (Performance) will have a 'performance engineer' system prompt")
print("")
print("  NEXT: Lesson 3 — Multi-turn conversations (memory basics)")

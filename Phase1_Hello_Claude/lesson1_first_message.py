# pyre-ignore-all-errors
"""
╔══════════════════════════════════════════════════════════════════╗
║        PHASE 1 — LESSON 1: Your Very First Claude API Call      ║
╚══════════════════════════════════════════════════════════════════╝

GOAL: Send a message to Claude and get a reply. That's it.

WHAT YOU'LL LEARN:
  ✅ What the Anthropic "Messages API" is
  ✅ What a "model", "role", "content", and "max_tokens" mean
  ✅ How to use your API key safely with .env
  ✅ What "tokens" are and why they matter for cost

HOW TO RUN:
  python Phase1_Hello_Claude/lesson1_first_message.py
"""

import os
from dotenv import load_dotenv  # type: ignore
import anthropic

# ── Load your secret API key from the .env file ──────────────────
# NEVER hardcode your key directly in code. Always use .env.
load_dotenv()

# ── Create the client ─────────────────────────────────────────────
# This is your connection to Anthropic's servers.
# Think of it like opening a phone app — now you can make calls.
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

print("=" * 60)
print("  LESSON 1: First Message to Claude")
print("=" * 60)

# ── Send a message ────────────────────────────────────────────────
#
#  client.messages.create() is THE core function you'll use forever.
#
#  Parameters explained:
#  ┌──────────────┬─────────────────────────────────────────────┐
#  │ model        │ Which version of Claude to use.             │
#  │              │ "claude-sonnet-4-20250514" = best balance   │
#  │              │ of intelligence and speed.                  │
#  ├──────────────┼─────────────────────────────────────────────┤
#  │ max_tokens   │ Maximum length of Claude's reply.           │
#  │              │ 1 token ≈ 0.75 words. 1024 = ~750 words.   │
#  ├──────────────┼─────────────────────────────────────────────┤
#  │ messages     │ The conversation history. A list of turns.  │
#  │              │ "role" = who is speaking (user or assistant)│
#  │              │ "content" = what they said                  │
#  └──────────────┴─────────────────────────────────────────────┘

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello Claude! I am learning to build AI agents. "
                       "Please explain what a Pull Request is in GitHub "
                       "in exactly 3 sentences. Keep it simple."
        }
    ]
)

# ── Read the response ─────────────────────────────────────────────
# response.content is a list of "content blocks".
# For a simple text reply, we access [0].text
print("\n📨 Claude says:\n")
print(response.content[0].text)

# ── BONUS: Inspect the full API response ─────────────────────────
# This is very important — understand every field!
print("\n" + "─" * 60)
print("📊 API Response Details:")
print(f"  Model used      : {response.model}")
print(f"  Input tokens    : {response.usage.input_tokens}")
print(f"  Output tokens   : {response.usage.output_tokens}")
total = response.usage.input_tokens + response.usage.output_tokens
print(f"  Total tokens    : {total}")
print(f"  Stop reason     : {response.stop_reason}")
print("─" * 60)
print("\n💡 CONCEPT — What are tokens and costs?")
print("  Claude Sonnet 3.5 costs approximately:")
print("  - $3.00 per 1 million INPUT tokens")
print("  - $15.00 per 1 million OUTPUT tokens")
print(f"  This single call cost ≈ ${(response.usage.input_tokens * 0.000003 + response.usage.output_tokens * 0.000015):.6f}")
print("\n  In a real production system with 100s of PR reviews/day,")
print("  tracking token usage is critical to control costs.")
print("  (This is exactly what the JD means by 'cost-performance trade-offs')")

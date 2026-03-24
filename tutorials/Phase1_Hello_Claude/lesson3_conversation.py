# pyre-ignore-all-errors
"""
╔══════════════════════════════════════════════════════════════════╗
║        PHASE 1 — LESSON 3: Multi-Turn Conversations             ║
╚══════════════════════════════════════════════════════════════════╝

GOAL: Build a simple back-and-forth conversation with Claude —
      a basic chatbot. This teaches you how Claude "remembers"
      previous messages within a single session.

WHAT YOU'LL LEARN:
  ✅ How the messages array builds up conversation history
  ✅ Why Claude has NO memory by default (stateless API)
  ✅ How YOU must manually maintain the conversation history
  ✅ The concept of "context window" (Claude's short-term memory limit)

JD CONNECTION:
  The JD says: "reasoning chains, memory handling."
  This lesson is the foundation of memory handling.

HOW TO RUN:
  python Phase1_Hello_Claude/lesson3_conversation.py
"""

import os
from dotenv import load_dotenv  # type: ignore
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("=" * 60)
print("  LESSON 3: Multi-Turn Conversation (Simple Chatbot)")
print("  Type 'quit' to exit")
print("=" * 60)

# ── CRITICAL CONCEPT: The messages list IS the memory ─────────────
#
#  Claude's API is STATELESS — it remembers NOTHING between API calls.
#  You must send the FULL conversation history every single time.
#
#  messages = [
#    { "role": "user",      "content": "first user message" },
#    { "role": "assistant", "content": "first claude reply" },
#    { "role": "user",      "content": "second user message" },
#    { "role": "assistant", "content": "second claude reply" },
#    ...
#  ]
#
#  Growing this list and sending it each time = "memory"

conversation_history = []  # Start with empty history

SYSTEM_PROMPT = """You are an expert code reviewer helping a junior developer 
learn code review. You are teaching them step by step. Be encouraging 
but precise about technical issues."""

while True:
    # Get user input
    user_input = input("\n👤 You: ").strip()
    
    if user_input.lower() == 'quit':
        print("\n👋 Chat ended. See conversation summary below.")
        break
    
    if not user_input:
        continue
    
    # Add the user's message to history
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Send the ENTIRE history to Claude every time
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=conversation_history   # <-- This is the KEY line
    )
    
    # Extract Claude's reply
    claude_reply = response.content[0].text
    
    # Add Claude's reply to history so it's included next time
    conversation_history.append({
        "role": "assistant",
        "content": claude_reply
    })
    
    print(f"\n🤖 Claude: {claude_reply}")
    
    # Show live token usage
    total_tokens = response.usage.input_tokens + response.usage.output_tokens
    print(f"\n   [Tokens this call: {total_tokens} | "
          f"Context size: {response.usage.input_tokens} input tokens]")


# ── Show what the full conversation history looks like ────────────
if conversation_history:
    print("\n\n" + "─" * 60)
    print("📊 WHAT THE API RECEIVED ON THE LAST CALL:")
    print("   (This is the raw messages array Claude sees)")
    print("─" * 60)
    for i, msg in enumerate(conversation_history):
        role = "👤 USER" if msg["role"] == "user" else "🤖 CLAUDE"
        content_preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
        print(f"  [{i+1}] {role}: {content_preview}")
    
    print(f"\n  Total turns: {len(conversation_history) // 2}")
    print("\n💡 KEY INSIGHT:")
    print("  Notice how every call sends MORE tokens as the")
    print("  conversation grows? This is the Context Window problem.")
    print("  In Phase 4, LangGraph manages this for you automatically.")

# pyre-ignore-all-errors
"""
╔══════════════════════════════════════════════════════════════════╗
║               PHASE 1 — Complete Runner                         ║
║         Run all 4 lessons in sequence with explanations         ║
╚══════════════════════════════════════════════════════════════════╝

This script runs all Phase 1 lessons one by one.
It gives you a chance to press Enter between each lesson.

HOW TO RUN:
  python Phase1_Hello_Claude/run_phase1.py
"""

import os
import sys  # type: ignore

def pause(msg=""):
    if msg:
        print(f"\n{'─' * 60}")
        print(f"  {msg}")
        print(f"{'─' * 60}")
    input("\n  ▶  Press Enter to continue... ")
    print("\n" * 2)

def run_lesson(module_path: str, label: str):
    """Dynamically run a lesson script."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("lesson", module_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    try:
        spec.loader.exec_module(mod)  # type: ignore
    except SystemExit: 
        pass

# ── Detect path ───────────────────────────────────────────────────
base = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("  🚀 PHASE 1: Learning the Anthropic Claude API")
print("  4 Lessons | ~30 minutes to complete")
print("=" * 60)
print()
print("  What you'll learn:")
print("  Lesson 1 → Your first Claude API call")
print("  Lesson 2 → System prompts & role prompting")
print("  Lesson 3 → Multi-turn conversations (memory basics)")
print("  Lesson 4 → Structured JSON output (automation-ready)")
print()
print("  After Phase 1, you will understand the EXACT building blocks")
print("  of every AI agent system in the world.")

pause("STARTING LESSON 1: First Message to Claude")
run_lesson(os.path.join(base, "lesson1_first_message.py"), "Lesson 1")

pause("LESSON 1 DONE ✅  Starting LESSON 2: System Prompts")
run_lesson(os.path.join(base, "lesson2_system_prompts.py"), "Lesson 2")

pause("LESSON 2 DONE ✅  Starting LESSON 3: Conversations\n  "
      "NOTE: This is INTERACTIVE. Type anything, then 'quit' to exit.")
run_lesson(os.path.join(base, "lesson3_conversation.py"), "Lesson 3")

pause("LESSON 3 DONE ✅  Starting LESSON 4: Structured JSON Output")
run_lesson(os.path.join(base, "lesson4_structured_output.py"), "Lesson 4")

print("\n" + "=" * 60)
print("  🎉 PHASE 1 COMPLETE!")
print("=" * 60)
print("""
  You now understand the FULL Anthropic Claude API:

  ✅ Messages API (model, max_tokens, messages)
  ✅ System Prompts (personality & behavior control)
  ✅ Multi-turn Conversations (how memory works)
  ✅ Structured JSON Output (automation-ready responses)

  These 4 concepts are used in EVERY AI agent system.

  ──────────────────────────────────────────────────
  NEXT: Phase 2 — Advanced Prompt Engineering
  You'll build production-quality prompts using:
  → XML tags (Claude's preferred structure)
  → Few-shot prompting (teaching by example)
  → Chain-of-Thought (making Claude think step by step)
  ──────────────────────────────────────────────────

  Tell me: "Start Phase 2" to continue!
""")

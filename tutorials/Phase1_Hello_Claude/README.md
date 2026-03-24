# 📖 Phase 1: Hello Claude & The Anthropic API

**Goal:** Establish a rock-solid foundation in the Anthropic Messages API, preparing for complex multi-agent reasoning and automation code reviews.

---

## 🎯 Direct JD Alignment (Apex AI - Claude Specialist)

This phase directly proves your capability against the following requirements from the Apex AI Job Description:

1. **"Proven hands-on experience working with Claude (Anthropic API)."**
   - You used the official `anthropic` Python SDK to interact with the `claude-sonnet-4-20250514` model.
2. **"Implement structured outputs (JSON schemas)."**
   - In Lesson 4, we forced Claude to abandon free-text and return strict, parsable JSON. This is the bedrock of any automated pipeline.
3. **"Strong understanding of AI system evaluation, optimization, and cost-performance trade-offs."**
   - By analyzing `response.usage.input_tokens` and `output_tokens` in Lesson 1, we understand exactly how pricing works (input vs output differences) and how conversation context size impacts budget exactly as demanded by "cost-performance trade-offs".
4. **"Architect multi-step Agent Workflows including memory handling."**
   - Lesson 3 demonstrated how the API is entirely stateless. Building the `conversation_history` array manually is your first direct implementation of "memory handling".

---

## 📂 Lesson Breakdown

### `lesson1_first_message.py` (Core API & Cost Tracking)
- Taught the `client.messages.create()` execution.
- Configured `.env` for secure credential injection.
- Monitored Input/Output tokens to calculate raw cost per API execution.

### `lesson2_system_prompts.py` (Role Prompting)
- Showcased how passing a rigid `system` parameter completely alters Claude’s output. 
- Transitioned Claude from a "Friendly Tutor" to a strict "Senior Code Reviewer".

### `lesson3_conversation.py` (Memory Management)
- Created an interactive while-loop Chatbot.
- Solidified the concept of "The Context Window" — realizing that memory is just appending past interactions explicitly into every new API request.

### `lesson4_structured_output.py` (Automation Enablers)
- Explored why generic conversation is useless for CI/CD pipelines.
- Implemented a JSON-enforced structure so our Python code could parse review outputs programmatically (`json.loads()`).

---

## 🚀 How to Run Phase 1

To run all modules back-to-back testing your knowledge:
```bash
python run_phase1.py
```

***

**Next Step ➡️ Phase 2 (Prompt Engineering)** where we adapt these concepts using XML tags, Few-Shot prompting, and Chain-of-Thought (CoT).

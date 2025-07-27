import os
import json
import re
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# --- Load Environment Variables ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

# --- LLM Setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite-preview-06-17",
    temperature=0.5,
    google_api_key=api_key
)

# --- Prompt Template ---
prompt = ChatPromptTemplate.from_template(
    """
You are the world’s foremost technical interview evaluator—an elite, zero‑error decision engine for a critical AI interview system.

Your mission: **scrutinize every candidate response** and decide *exactly* what to do next, with no room for error, fluff, or hallucination.

---

🎯 **Output** must be a **pure JSON object** with:

1. **action**: *exactly one* of:
   - **"follow_up"**  
     The answer is correct but can be probed deeper with a focused, technical question.
   - **"wrong_answer"**  
     The answer contains factual errors, misunderstandings, or missing core concepts—correct them.
   - **"Repeat_question"**  
     The candidate asked for repetition or showed clear confusion about the question.
   - **"Elaborate"**  
     The response was too brief or generic; request specific technical details or examples.
   - **"No_question"**  
     The answer is comprehensive, correct, and would add no value to probe further.

2. **trail_summary**: 1–2 sentences, strictly factual, summarizing *the interview’s trajectory* so far.

3. **context_summary**: 1 sentence, neutral, summarizing *only* what the candidate just said.

---

📥 **Inputs**:

- **Full Q&A Trail (timestamped):**  
  {{question_answer_trail}}

- **Latest Transcript:**  
  {{latest_transcript}}

---

⛔ **Rules**:

- **Only** output JSON—no markdown, no explanations, no extra text.
- **No hallucinations**, **no invented details**, **no unnecessary noise**.
- Be **precise**, **concise**, and **blindingly accurate**.
- Use **only** the five valid "action" labels above.
"""
)


# --- Regex JSON Extractor ---
def extract_json_block(text: str) -> str:
    json_candidates = re.findall(r'\{[\s\S]*?\}', text)
    for candidate in json_candidates:
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            continue
    return ""


# --- Action Handlers ---
from app.services.follow_up_gen_new_update import generate_structured_followups
async def handle_follow_up(latest_transcript: str, question_answer_trail: str):
    result = await generate_structured_followups(latest_transcript,question_answer_trail)
    print("📌 Deciding to ask a follow-up based on latest response.",result)
    return result

from app.services.wrong_answer import handle_wrong_answer_async
async def handle_wrong_answer(latest_transcript: str, question_answer_trail: str):
    result = await handle_wrong_answer_async(latest_transcript,question_answer_trail)
    print("⚠️ Candidate seems to have answered incorrectly. Prompting clarification.",result)
    return result

from app.services.repeat_question import handle_repeat_question_async
async def handle_repeat_question(latest_transcript: str, question_answer_trail: str):
    result = await handle_repeat_question_async(question_answer_trail)
    print("🔁 Candidate asked for a repeat or didn’t hear the question clearly.",result)
    return result

from app.services.elaborate import handle_elaborate_async
async def handle_elaborate(latest_transcript: str, question_answer_trail: str):
    result = await handle_elaborate_async(latest_transcript,question_answer_trail)
    print("📎 Asking the candidate to elaborate further.",result)
    return result

def handle_no_question(latest_transcript: str, question_answer_trail: str):
    return {
        "priority": 0,
        "discussion": "All Fine. No further probing needed.",
        "status": 200,
    }

# --- Decision Controller ---
async def make_decision(question_trail: str, transcript: str,id:str):
    chain = prompt | llm
    raw = ""  # ensure raw is always defined

    try:
        response = chain.invoke({
            "latest_transcript": transcript,
            "question_answer_trail": question_trail
        })

        raw = str(response.content or "").strip()
        print(f"\n🧾 Raw LLM Output:\n{raw}\n")

        json_block = extract_json_block(raw)
        if not json_block:
            raise ValueError("No valid JSON object found in LLM response.")

        parsed = json.loads(json_block)
        action = parsed.get("action", "").strip()
        trail_summary = parsed.get("trail_summary", "No trail summary.")
        context_summary = parsed.get("context_summary", "No context summary.")

        combined_summary = (
            f"\n--- CONTEXT ---\n"
            f"📘 Latest Transcript: {transcript}\n"
            f"🧭 Trail Summary: {trail_summary}\n"
            f"🗒️ Context Summary: {context_summary}\n"
            f"----------------\n"
        )

        print(combined_summary)

        decision_map = {
            "follow_up": lambda: handle_follow_up(transcript, question_trail),
            "wrong_answer": lambda: handle_wrong_answer(transcript, question_trail),
            "Repeat_question": lambda: handle_repeat_question(transcript, question_trail),
            "Elaborate": lambda: handle_elaborate(transcript, question_trail),
            "No_question": lambda: handle_no_question(transcript, question_trail),
        }

        if action in decision_map:
            print(f"\n🤖 LLM Decision: {action}")
            result = await decision_map[action]()
            print("🧩 Handler Output:", result)
            return result
        else:
            print(f"❌ Unexpected action from LLM: '{action}'\n🧾 Raw response: {json_block}")
            return {"priority": 0, "discussion": "Unknown action", "status": 520}

    except Exception as e:
        print(f"❗ Error during LLM decision: {e}\n↪ Raw content was:\n{raw}")
        return {"priority": 0, "discussion": "Exception occurred", "status": 500}

# # --- Run ---
# if __name__ == "__main__":
#     dummy_trail = "[00:01] Q: What is Docker? A: It's a container tool for deployment."
#     dummy_transcript = "I used Docker to deploy apps, it works on images and containers."
#     make_decision(dummy_trail, dummy_transcript,"001")

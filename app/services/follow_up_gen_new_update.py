import os
import json
import asyncio
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# --- Step 1: Load Environment Variables ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

# --- Step 2: LLM Setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite-preview-06-17",
    temperature=0.4,
    google_api_key=api_key
)

# --- Step 3: Prompt Template ---
prompt = ChatPromptTemplate.from_template(
    """
You are a highly intelligent and experienced AI assistant trained to simulate human interviewers.
You are reviewing a candidate's spoken response and determining whether a follow-up question is required.

Your task is to:
1. Analyze the latest transcript for gaps in reasoning, shallow explanations, incorrect use of terminology, or weak understanding.
2. Consider the previous Q&A trail to avoid repeating already addressed topics.
3. Formulate a creative, specific follow-up question **only if needed**.

When generating follow-ups:
- Make it realistic, situational, and sound like a human interviewer's natural curiosity.
- Avoid robotic phrasing like "Can you elaborate?" or "Please explain more".
- Use punctuation so TTS can parse your speech properly.
- Be brief and impactful — no fluff.

You MUST return a structured JSON object using this format:

{{
  "priority": integer,  // 0 if no follow-up, else 60 + score (where score ∈ [1, 5])
  "discussion": string, // follow-up question OR "No follow-up needed."
  "status": integer     // 200 if nothing to ask, 206 if follow-up generated
}}

Scoring scale:
- 1: Mild clarification or curiosity
- 2–3: Moderate gap or technical vagueness
- 4: Significant reasoning issue or misinterpretation
- 5: Critical misunderstanding or missed concept

Rules:
- If the answer is confident, clear, and well-structured: return priority=0, status=200, discussion="No follow-up needed."
- If there's a strong reason to ask, return a specific question, and compute: priority = 60 + score, status = 206

---
📄 Latest Transcript:
{{latest_transcript}}

---
🧠 Previous Q&A Trail:
{{question_answer_trail}}

---
📤 Respond ONLY with a valid JSON object. Do not include markdown, prose, or code blocks.
"""
)

# --- Step 4: Regex-based JSON extractor ---
def extract_json(raw_text: str) -> str:
    # Handles code block + normal cases
    match = re.search(r"```(?:json)?\s*({.*})\s*```", raw_text, re.DOTALL)
    if match:
        return match.group(1)
    return raw_text.strip()

# --- Step 5: Follow-up Generator ---
async def generate_structured_followups(latest_transcript: str, question_answer_trail: str) -> dict:
    chain = prompt | llm

    try:
        response = await chain.ainvoke({
            "latest_transcript": latest_transcript,
            "question_answer_trail": question_answer_trail
        })
        raw = str(response.content or "").strip()
        print("\n🧾 Raw LLM Output:\n", raw)

        clean = extract_json(raw)
        parsed = json.loads(clean)

        if (
            isinstance(parsed, dict) and
            "priority" in parsed and isinstance(parsed["priority"], int) and
            "discussion" in parsed and isinstance(parsed["discussion"], str) and
            "status" in parsed and isinstance(parsed["status"], int)
        ):
            return parsed

        raise ValueError("Parsed content missing expected keys.")
    except Exception as e:
        print(f"\n❗ Error during LLM decision: {e}")
        return {
            "priority": 0,
            "discussion": "LLM failed to generate a valid response.",
            "status": 500
        }

# # --- Step 6: Test Runner ---
# if __name__ == "__main__":
#     async def main():
#         latest = "I created a REST API using Flask and connected it to a PostgreSQL database for a small finance dashboard."
#         trail = "Q: Can you tell me about a recent backend project?\nA: Yes, I used Flask and Postgres..."

#         result = await generate_structured_followups(latest, trail)

#         print("\n✅ Final Structured Response:")
#         print(json.dumps(result, indent=2))

#     asyncio.run(main())

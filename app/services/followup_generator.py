import os
import json
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# --- Load environment variables --
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

# --- Setup Gemini LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite-preview-06-17",
    temperature=0.4,
    google_api_key=api_key
)

# --- Follow-up Prompt Template ---
prompt = ChatPromptTemplate.from_template("""
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
  "priority": integer,
  "discussion": string,
  "status": integer
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
""")

# --- Extract JSON ---
def extract_json(raw_text: str) -> str:
    match = re.search(r"```(?:json)?\s*({.*})\s*```", raw_text, re.DOTALL)
    if match:
        return match.group(1)
    return raw_text.strip()

# --- Function to Generate Follow-up ---
async def generate_followup(user_answer: str, qa_trail: str = "") -> str:
    """
    Generates a follow-up question based on the given answer.
    Returns only the discussion (question or 'No follow-up needed.').
    """

    chain = prompt | llm

    try:
        response = await chain.ainvoke({
            "latest_transcript": user_answer,
            "question_answer_trail": qa_trail
        })

        raw = str(response.content or "").strip()
        print("\n🧾 Raw LLM Output:\n", raw)

        clean = extract_json(raw)
        parsed = json.loads(clean)

        if isinstance(parsed, dict) and "discussion" in parsed:
            return parsed["discussion"]

        raise ValueError("Parsed content missing 'discussion' field.")

    except Exception as e:
        print(f"\n❗ Error generating follow-up: {e}")
        return "No follow-up needed."

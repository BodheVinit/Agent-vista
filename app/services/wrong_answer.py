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

# --- Step 3: Define Prompt Template with Priority ---
wrong_answer_prompt = ChatPromptTemplate.from_template("""
You are an expert technical interviewer in a fast-paced AI interview.
The candidate just gave an incorrect or incomplete answer. Your task:

1. Provide a concise, natural-language correction or hint as if speaking directly to the candidate.
2. Assign a status code:
   - 404: Incorrect or unsatisfied.
3. Set a priority (0–100) indicating how urgent it is for the candidate to correct this mistake:
   - Higher means more immediate.

Return **only** a JSON object in this format:
```json
{{
  "status": 404,
  "explanation": "Your corrective feedback to the candidate.",
  "priority": 80 // This is strict,
}}
```

Latest candidate response:
"{latest_transcript}"

Relevant previous Q&A trail:
"{question_answer_trail}"
""")

# --- JSON Extraction Helper ---
def extract_json_from_llm_response(text: str) -> dict:
    """
    Extracts JSON from LLM response, stripping markdown if needed.
    """
    match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    json_str = match.group(1) if match else text.strip()
    try:
        data = json.loads(json_str)
        # Ensure all keys exist
        return {
            "status": data.get("status", 500),
            "explanation": data.get("explanation", ""),
            "priority": data.get("priority", 0)
        }
    except json.JSONDecodeError:
        return {"status": 500, "explanation": "Could not parse LLM response.", "priority": 0}

# --- Async Wrong Answer Handler ---
async def handle_wrong_answer_async(latest_transcript: str, question_answer_trail: str) -> dict:
    chain = wrong_answer_prompt | llm
    try:
        response = await chain.ainvoke({
            "latest_transcript": latest_transcript,
            "question_answer_trail": question_answer_trail
        })
        raw = str(response.content or "").strip()
        print("\n📨 Raw LLM response:\n", raw)

        result = extract_json_from_llm_response(raw)
        print(f"\n✅ Parsed Response: status={result['status']}, priority={result['priority']}")
        return result
    except Exception as e:
        print(f"\n❗ Unexpected error: {e}")
        return {"status": 500, "explanation": str(e), "priority": 0}

# # --- Manual Test Section ---
# if __name__ == "__main__":
#     async def test():
#         trail = "12:00 Q: What is binary search? A: It's used to find something in a sorted list quickly."
#         latest = "Binary search checks each element one by one."
#         result = await handle_wrong_answer_async(latest, trail)
#         print("\n🧪 Final Output:", result)

#     asyncio.run(test())

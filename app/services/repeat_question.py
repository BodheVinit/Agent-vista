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
repeat_question_prompt = ChatPromptTemplate.from_template("""
You are a helpful AI-powered interviewer assistant in a fast-paced technical interview.
The candidate has just asked you to repeat the question. Your task:

1. Politely acknowledge their request.
2. Creatively and clearly rephrase or repeat the last question, maintaining its original intent.
3. You may include brief encouragement (e.g., "Take your time.", "Let me repeat that for clarity.").
4. The tone should feel natural, supportive, and aligned with the flow of a live interview.

Return only the following JSON format:
```json
{{
  "status": 506,
  "discussion": "Your friendly, reworded or repeated version of the last question.",
  "priority": 1000 // give priority 1000
}}
```

Relevant previous Q&A trail:
"{question_answer_trail}"
""")

# --- JSON Extraction Helper ---
def extract_json_from_llm_response(text: str) -> dict:
    match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    json_str = match.group(1) if match else text.strip()
    try:
        data = json.loads(json_str)
        return {
            "status": data.get("status", 500),
            "discussion": data.get("discussion", ""),
            "priority": data.get("priority", 0)
        }
    except json.JSONDecodeError:
        return {"status": 500, "discussion": "Could not parse LLM response.", "priority": 0}

# --- Async Repeat Question Handler ---
async def handle_repeat_question_async(question_answer_trail: str) -> dict:
    chain = repeat_question_prompt | llm
    try:
        response = await chain.ainvoke({"question_answer_trail": question_answer_trail})
        raw = str(response.content or "").strip()
        print("\n📨 Raw LLM response:\n", raw)

        result = extract_json_from_llm_response(raw)
        print(f"\n✅ Parsed Response: status={result['status']}, priority={result['priority']}")
        return result
    except Exception as e:
        print(f"\n❗ Unexpected error: {e}")
        return {"status": 500, "discussion": str(e), "priority": 0}

# # --- Manual Test Section ---
# if __name__ == "__main__":
#     async def test():
#         trail = "12:01 Q: Can you explain how binary search works?"
#         result = await handle_repeat_question_async(trail)
#         print("\n🧪 Final Output:", result)

#     asyncio.run(test())

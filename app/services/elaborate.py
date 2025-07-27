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

# --- Step 2: Initialize LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite-preview-06-17",
    temperature=0.4,
    google_api_key=api_key
)

# --- Step 3: Enhanced Prompt Template for Elaborate Handler ---
elaborate_prompt = ChatPromptTemplate.from_template(
    """
You are an expert technical interviewer whose role is to guide candidates from superficial answers into deeper insight.

The candidate’s last response was too brief or generic. Your task:

1. **Generate a concise, context‑rich scenario or example** that builds directly on a concept the candidate mentioned.
2. **Pose a guiding follow‑up question or hint**—never just correct, always invite expansion.
3. **Return a strict JSON object** with:
   - "status": 200 (okay to elaborate) or 300 (urgent elaboration needed)
   - "discussion": 1–2 sentences tying the scenario to their exact words
   - "priority": an integer 0–100 indicating how critical it is to follow up now

📅 Inputs  
- `latest_transcript`: the candidate’s most recent utterance  
- `question_answer_trail`: the full timestamped Q&A history

⛘ Rules  
- **Only** output valid JSON—no markdown, no commentary.  
- **discussion** must reference a specific term or phrase from `latest_transcript`.  
- **No hallucinations**, **no extra fields**, **no filler**.  
- **discussion** limited to 2 sentences max.

Example output:
```json
{{
  "status": 300,
  "discussion": "You mentioned using a three‑way handshake for the TCP connection. Imagine you’re debugging a failed handshake under high load—what TCP flags or packet captures would you examine first?",
  "priority": 85
}}
```
"""
)

# --- JSON Extraction Helper ---
def extract_json_block(text: str) -> dict:
    """
    Extracts JSON block from markdown-wrapped LLM response.
    """
    match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    json_str = match.group(1) if match else text.strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"status":500, "discussion":"Could not parse elaboration.", "priority":0}

# --- Async Handler Function ---
async def handle_elaborate_async(latest_transcript: str, question_answer_trail: str) -> dict:
    chain = elaborate_prompt | llm
    try:
        response = await chain.ainvoke({
            "latest_transcript": latest_transcript,
            "question_answer_trail": question_answer_trail
        })
        raw = str(response.content or "").strip()
        print("\n📨 Raw LLM response:\n", raw)

        result = extract_json_block(raw)
        print(f"\n✅ Parsed Elaborate Response: status={result.get('status')}, priority={result.get('priority')}")
        return result
    except Exception as e:
        print(f"\n❗ Error in handle_elaborate_async: {e}")
        return {"status":500, "discussion":str(e), "priority":0}

# --- Manual Test Section ---
# if __name__ == "__main__":
#     async def test():
#         trail = "00:05 - Q: What is a REST API? A: It's an interface for HTTP calls."
#         latest = "It allows communication between client and server."
#         result = await handle_elaborate_async(latest, trail)
#         print("\n🧪 Final Output:", result)

#     asyncio.run(test())

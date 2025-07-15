from collections import deque
import os
import json
from rapidfuzz import fuzz
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import re
load_dotenv()

# ✅ LangChain + Gemini Setup
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite-preview-06-17",
    temperature=0.5,
)

# ✅ Prompt with structured JSON output request
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template(
    """
You are a highly intelligent and experienced interview assistant with deep domain knowledge.
You are helping conduct a technical interview.

Don't deviate much from the answer of what the speaker has spoken, the speaker might have made some mistakes, if it's there
flag that mistake, this also counts as a follow-up and give it a score of 5 as it should be asked 
and don't be too harsh on the student, but give a situation related to the one he has spoken and remmeber if this 
transcript has nothing to ask, generate nothing, just empty format file, not needed if things are not required
to be asked

Don't overuse can you elaborate can you elaborate, just me more creative in asking the questions, 
you mustn't sound like bot any day, you should act like human, give punctuations in questions, hence the tts can 
understand where to pause and continue

Given the transcript of a candidate's recent response, generate exactly **one** thoughtful follow-up question **only if**:
- The candidate's answer lacks depth or specificity
- There are unclear, ambiguous, or unexplored areas
- The candidate sounds uncertain or overly confident without explanation

Do **not** ask a follow-up if the answer is confident, complete, and well-reasoned.

Your follow-up question should:
- Be realistic and situation-based, like a human interviewer probing further
- Mention hypothetical scenarios or edge cases where needed
- Avoid repetition or generic phrasing
- Use natural, conversational language

Each follow-up must include:
- `"question"`: the exact question to ask
- `"score"`: integer from 0 to 5 (how important it is to ask this follow-up)

If no follow-up is needed, return an empty list `[]`.

---
Transcript:
{transcript}

---
Return ONLY a valid JSON array in this format:

[
  {{ "question": "string", "score": integer }},
  ...
]
"""
)

# ✅ Generates structured follow-ups with score
def extract_json(raw_text):
    # Remove Markdown code block if present
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw_text, re.DOTALL)
    if match:
        return match.group(1)
    return raw_text.strip()  # fallback to raw text if no code block

def generate_structured_followups(transcript_chunk):
    chain = prompt | llm
    response = chain.invoke({"transcript": transcript_chunk})
    raw = str(response.content or "").strip()

    try:
        clean_json = extract_json(raw)
        parsed = json.loads(clean_json)
        validated = [
            item for item in parsed
            if isinstance(item, dict)
            and "question" in item
            and "score" in item
            and isinstance(item["score"], int)
            and 1 <= item["score"] <= 5
        ]
        return validated
    except json.JSONDecodeError:
        print("❌ JSON decoding failed. Raw output was:\n", raw)
        return []


# ✅ InterviewState using JSON questions
class InterviewState:
    def __init__(self, predefined_questions):
        self.transcript = []
        self.predefined_questions = deque(predefined_questions)
        self.asked_questions = []

    def update_transcript(self, chunk):
        self.transcript.append(chunk)

    def already_asked(self, question):
        return any(fuzz.ratio(question.lower(), asked.lower()) > 85 for asked in self.asked_questions)

    def pick_followup(self, generated_questions):
        for q in generated_questions:
            if not self.already_asked(q["question"]):
                return q
        return None

    def pick_next_question(self, transcript_chunk):
        generated_questions = generate_structured_followups(transcript_chunk)
        followup = self.pick_followup(generated_questions)
        if followup:
            self.asked_questions.append(followup["question"])
            return "followup", followup
        elif self.predefined_questions:
            next_q = self.predefined_questions.popleft()
            self.asked_questions.append(next_q)
            return "predefined", {"question": next_q, "score": None}
        else:
            return "end", {"question": "Interview completed 🎉", "score": None}

# # 🧪 Example usage
# if __name__ == "__main__":
#     predefined = [
#         "Tell me about yourself.",
#         "What is your biggest strength?",
#         "Describe your last project.",
#     ]

#     agent = InterviewState(predefined)

#     # Simulate transcript chunk input
#     chunk = "I used Docker to deploy my latest app to production and made use of images and containers."
#     agent.update_transcript(chunk)

#     qtype, question_data = agent.pick_next_question(chunk)

#     print(f"\n🤖 Asking ({qtype}): {question_data['question']}")
#     if question_data["score"] is not None:
#         print(f"📊 Relevance Score: {question_data['score']}")

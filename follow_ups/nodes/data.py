# load_dotenv reads .env and loads the keys into environment
from dotenv import load_dotenv
load_dotenv()

from transcipt import transcript_exp  # your transcript source
import re
from typing import Dict, List, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# -- GLOBAL MEMORY TO TRACK UNIQUE QUESTIONS --
seen_questions: set[str] = set()

# -- MODEL SETUP --
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

# -- HELPER FUNCTION TO CLEAN RESPONSES --
def clean_content(content):
    if isinstance(content, list):
        for item in content:
            if isinstance(item, str):
                return item.strip()
            elif isinstance(item, dict) and "text" in item:
                return item["text"].strip()
        return ""
    elif isinstance(content, str):
        return content.strip()
    return ""

# -- STATE SCHEMA --
class InterviewState(TypedDict):
    transcript: str
    previous_questions: List[str]
    generated_questions: List[str]

# -- LANGGRAPH NODE FUNCTION --
def generate_unique_questions_node(state: InterviewState) -> InterviewState:
    transcript: str = state["transcript"]
    previous_qas: List[str] = state.get("previous_questions", [])

    system_prompt = (
        "You are one of the most efficient and well-regarded tech interviewers. "
        "Avoid duplication. Rate each question between 0 and 1. "
        "Prefer clarity, coverage, and relevance to the transcript."
    )

    chat = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            "Based on the following transcript, generate 3 unique tech interview questions "
            "with a confidence score between 0-1.\n\n"
            "Format: Q. <question>? Score: <score>\n\nTranscript:\n"
            f"{transcript}"
        ))
    ]

    response = model.invoke(chat)
    output = clean_content(response.content)

    # Extract using regex
    pattern = re.compile(r"Q\.\s*(.+?)\?\s*Score:\s*([0-9.]+)", re.DOTALL)
    matches = pattern.findall(output)

    filtered_qas = []
    for question, score in matches:
        question = question.strip()
        try:
            score = float(score)
        except ValueError:
            continue
        if question.lower() not in (q.lower() for q in seen_questions) and score >= 0.4:
            filtered_qas.append((question, score))
            seen_questions.add(question)

    filtered_qas.sort(key=lambda x: -x[1])  # Highest score first

    # Update state
    state["generated_questions"] = [q for q, _ in filtered_qas]
    state["previous_questions"] = previous_qas + [q for q, _ in filtered_qas]

    return state

# -- LANGGRAPH SETUP --
builder = StateGraph(state_schema=InterviewState)

builder.add_node("generate_questions", generate_unique_questions_node)
builder.set_entry_point("generate_questions")
builder.set_finish_point("generate_questions")

graph = builder.compile()

# -- SAMPLE TRANSCRIPT --
transcript = transcript_exp

# -- INITIAL STATE --
initial_state: InterviewState = {
    "transcript": transcript,
    "previous_questions": [],
    "generated_questions": []
}

# -- RUN GRAPH --
result = graph.invoke(initial_state)
print(result)

# -- PRINT RESULTS --
print("🧠 Generated Questions:\n")
for i, q in enumerate(result["generated_questions"], 1):
    print(f"{i}. {q}")

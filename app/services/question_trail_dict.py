import os
import json
import uuid
from typing import Literal, TypedDict, List, Optional
import redis.asyncio as redis  # Note the asyncio variant
from dotenv import load_dotenv
load_dotenv()
import asyncio

class AnswerChunk(TypedDict):
    role: Literal["human", "AI_Interviewer"]
    text: str


class QuestionDoc(TypedDict):
    id: str
    question: str
    answers: List[AnswerChunk]
    system_messages: List[str]


class AsyncQATrailManager:
    def __init__(self, redis_url=os.getenv('REDIS_PATH')):
        self.r = redis.from_url(redis_url, decode_responses=True)
        self.prefix = "qa:"

    def _key(self, qid: str) -> str:
        return f"{self.prefix}{qid}"

    async def create_question(self, question_text: str) -> str:
        qid = str(uuid.uuid4())
        doc: QuestionDoc = {
            "id": qid,
            "question": question_text,
            "answers": [],
            "system_messages": []
        }
        await self.r.set(self._key(qid), json.dumps(doc))
        return qid

    async def _get_doc(self, qid: str) -> Optional[QuestionDoc]:
        raw = await self.r.get(self._key(qid))  # 👈 Fix: await
        return json.loads(raw) if raw else None

    async def _set_doc(self, qid: str, doc: QuestionDoc) -> None:
        await self.r.set(self._key(qid), json.dumps(doc))

    async def append_answer(self, qid: str, answer_text: str, role: Literal["human", "AI_Interviewer"]) -> None:
        doc = await self._get_doc(qid)
        if not doc:
            raise KeyError(f"Invalid ID: {qid}")
        doc["answers"].append({"role": role, "text": answer_text})
        await self._set_doc(qid, doc)

    async def get_question_conversation(self, qid: str) -> str:
        doc = await self._get_doc(qid)
        if not doc:
            return "Invalid Question ID."

        lines = [f"Q ({qid}): {doc['question']}"]
        for idx, a in enumerate(doc["answers"], 1):
            lines.append(f"A{idx} ({a['role']}): {a['text']}")
        return "\n".join(lines)



# async def run_demo():
#     manager = AsyncQATrailManager()
#     qid = await manager.create_question("What is Redis?")
#     await manager.append_answer(qid, "Redis is an in-memory database.", role="human")
#     print(await manager.get_question_conversation(qid))
# asyncio.run(run_demo())

from fastapi import APIRouter
from app.models.questionManager import questionManager, QuestionManagerResponse, DecisionHeapItem
from app.models.followup import FollowUp
from app.services.question_trail_dict import AsyncQATrailManager
from app.services.decision_update import make_decision
from app.services.mongo import final_collection
from app.utils.text_speech_cloud import analyze_audio_url
from app.utils.heapq_compare import DecisionHeap

from datetime import datetime
from collections import defaultdict
import uuid

router = APIRouter()
qa_manager = AsyncQATrailManager()

# Store multiple heaps using candidate Qid as key
decision_heap_store: dict[str, DecisionHeap] = defaultdict(DecisionHeap)

# ----------------------------
# /interview/start endpoint
# ----------------------------
@router.post("/start", response_model=QuestionManagerResponse)
async def start_interview(request: questionManager):
    role = "AI_Interviewer"
    new_question = f"{role}: {request.questions}"
    candidate_id = request.candidate_id

    Qid = await qa_manager.create_question(question_text=new_question)

    return QuestionManagerResponse(
        Qid=Qid,
        status=201,
        priority=0,
        question=new_question,
        field_up_id="",
        audio_id=""
    )

# ----------------------------
# /interview/stream endpoint
# ----------------------------
@router.post("/stream")
async def stream_transcript(request: FollowUp):
    qid = request.Qid
    transcript = request.transcript
    candidate_id = request.candidate_id
    final_chunk = request.final_chunk  # ✅ this is guaranteed from FollowUp model

    # Step 1: Append transcript to conversation history
    await qa_manager.append_answer(qid, answer_text=transcript, role="human")

    # Step 2: Decision logic
    full_trail = await qa_manager.get_question_conversation(qid)
    decision_result = await make_decision(full_trail, transcript, qid)

    priority = decision_result.get("priority", 0)
    response = decision_result.get("discussion", "No discussion found.")
    status_code = decision_result.get("status", 200)

    # Step 3: Audio generation + Cloudinary upload
    field_up_id = str(uuid.uuid4())
    success, audio_id = await analyze_audio_url(response, field_up_id)

    if not success:
        return {"message": f"❌ Failed to process chunk {field_up_id}"}

    # Step 4: Push to heap
    heap_item = DecisionHeapItem(
        status=status_code,
        priority=priority,
        question=response,
        field_up_id=field_up_id,
        audio_id=audio_id
    )
    decision_heap_store[qid].push(heap_item, priority)

    # Step 5: Final chunk — respond with best item
    if final_chunk:
        top_item = decision_heap_store[qid].pop()
        del decision_heap_store[qid]  # ✅ Free memory

        final_doc = {
            "qid": qid,
            "candidate_id": candidate_id,
            "final_decision": top_item.dict(),
            "full_trail": full_trail,
            "timestamp": datetime.now()
        }
        await final_collection.insert_one(final_doc)

        return QuestionManagerResponse(
            Qid=qid,
            status=top_item.status,
            priority=top_item.priority,
            question=top_item.question,
            field_up_id=top_item.field_up_id,
            audio_id=top_item.audio_id
        )

    return {"message": f"✅ Chunk processed with priority={priority}"}

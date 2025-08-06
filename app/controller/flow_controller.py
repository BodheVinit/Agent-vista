from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.followup_generator import generate_followup
from app.services.backend_integration import send_to_backend

router = APIRouter()

class UserResponse(BaseModel):
    question_id: str
    answer: str

class InterviewQuestion(BaseModel):
    question: str

@router.post("/interview", response_model=InterviewQuestion)
async def interview_flow(user_response: UserResponse):
    """
    Orchestrates the interview flow between Member 4 (follow-up generator)
    and Member 6 (backend integration).
    """
    try:
        # 1. Get follow-up question from Member 4
        followup_question = await generate_followup(user_response.answer)

        # 2. Send the follow-up question to Member 6's backend
        await send_to_backend({
            "question_id": user_response.question_id,
            "question": followup_question
        })

        # 3. Return next question to frontend
        return {"question": followup_question}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

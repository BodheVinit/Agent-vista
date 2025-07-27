from pydantic import BaseModel

class FollowUp(BaseModel):
    Qid: str
    candidate_id: str
    transcript: str
    final_chunk: bool = False 
    
class followUpResonse(BaseModel):
    Qid: str
    status: int
    priority: int
    question: str
    field_up_id: str

class QDecisionResult(BaseModel):
    status: int
    priority: int
    question: str

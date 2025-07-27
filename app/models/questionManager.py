from pydantic import BaseModel

class questionManager(BaseModel):
    questions:str
    candidate_id:str

class QuestionManagerResponse(BaseModel):
    Qid: str
    status: int
    priority: int
    question: str
    field_up_id: str 
    audio_id: str    
class DecisionHeapItem(BaseModel):
    status: int
    priority: int
    question: str
    field_up_id: str
    audio_id: str

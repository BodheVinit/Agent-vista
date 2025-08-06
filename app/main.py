from fastapi import FastAPI
# from nodes import followup
# from nodes import question_Manager
from app.api.interview_router import router as interview_router
from app.controllers import flow_controller

app = FastAPI(
    title="Agent-Vista",
    description="An AI Agent build for taking Interviews",
    version="0.1.0"
)

# app.include_router(followup.router,prefix="/followup",tags=["follow-up"])
# app.include_router(question_Manager.router,prefix="/questionManager",tags=["questionManager"])
app.include_router(interview_router, prefix="/interview")
app.include_router(flow_controller.router,prefix ="/api", tags=["Flow Controller"])

# main.py (FastAPI Layer)
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from uuid import UUID
from v4 import ChatbotService
import uuid

app = FastAPI()
chatbot_service = ChatbotService()

# ======== Request/Response Models ========
class StartSessionRequest(BaseModel):
    amount_owed: float
    days_in_mora: int

class StartSessionResponse(BaseModel):
    session_id: str
    initial_message: str

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    current_amount_owed: float
    current_days_in_mora: int

class UpdateContextRequest(BaseModel):
    amount_owed: float | None = None
    days_in_mora: int | None = None

# ======== API Endpoints ========
@app.post("/start-session", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """Initialize a new negotiation session with financial context"""
    try:
        # Create new session
        session_id = chatbot_service.start_session({
            "amount_owed": request.amount_owed,
            "days_in_mora": request.days_in_mora
        })
        
        # Generate initial bot message
        initial_response = chatbot_service.process_message(
            session_id=session_id,
            user_input="[SYSTEM] Session started"  # Special trigger for initial message
        )
        
        return {
            "session_id": session_id,
            "initial_message": initial_response["response"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session initialization failed: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    """Handle ongoing conversation"""
    try:
        # Process user message
        result = chatbot_service.process_message(
            session_id=request.session_id,
            user_input=request.message
        )
        
        # Get updated financial context
        financial_context = chatbot_service.active_sessions[request.session_id]
        
        return {
            "response": result["response"],
            "current_amount_owed": financial_context["amount_owed"],
            "current_days_in_mora": financial_context["days_in_mora"]
        }
        
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired session ID"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message processing failed: {str(e)}"
        )

@app.patch("/sessions/{session_id}/context")
async def update_context(
    session_id: str,
    update: UpdateContextRequest
):
    """Manually update financial context"""
    try:
        context = chatbot_service.active_sessions[session_id]
        
        if update.amount_owed is not None:
            context["amount_owed"] = max(0, update.amount_owed)
            
        if update.days_in_mora is not None:
            context["days_in_mora"] = max(0, update.days_in_mora)
            
        return {"message": "Context updated successfully"}
        
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid session ID"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
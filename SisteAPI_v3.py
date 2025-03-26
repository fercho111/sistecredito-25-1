# main.py (FastAPI Layer)
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from SisteBot_v3 import ChatbotService
import uuid

app = FastAPI()
chatbot_service = ChatbotService()

# Session Management (In-memory example - use Redis in production)
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    amount_owed: float = None
    days_in_mora: int = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    current_amount_owed: float
    current_days_in_mora: int

@app.post("/chat", response_model=ChatResponse)
async def chat_handler(request: ChatRequest):
    # Session handling
    if not request.session_id or request.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "amount_owed": request.amount_owed or 0.0,
            "days_in_mora": request.days_in_mora or 0
        }
    else:
        session_id = request.session_id
    
    current_context = sessions[session_id]
    
    # Process message
    result = chatbot_service.process_message(
        user_input=request.message,
        financial_context=current_context
    )
    
    # Update session with new context
    sessions[session_id] = result["updated_context"]
    
    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        current_amount_owed=current_context["amount_owed"],
        current_days_in_mora=current_context["days_in_mora"]
    )

@app.post("/update-context/{session_id}")
async def update_context(
    session_id: str,
    amount_owed: float = None,
    days_in_mora: int = None
):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if amount_owed is not None:
        sessions[session_id]["amount_owed"] = amount_owed
    if days_in_mora is not None:
        sessions[session_id]["days_in_mora"] = days_in_mora
    
    return {"message": "Context updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
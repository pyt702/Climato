from fastapi import APIRouter, HTTPException
from schemas.dtos import ChatRequest, ChatResponse
from repositories.weather_repo import insert_conversation, get_recent_conversations
from graph.graph import app as graph_app
from datetime import datetime, timezone

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Fetch history for this session
        history = await get_recent_conversations(request.session_id)
        
        # Run LangGraph workflow
        result = await graph_app.ainvoke({
            "question": request.message,
            "history": history,
            "session_id": request.session_id
        })
        answer = result.get("final_answer", "I'm sorry, I couldn't process your request.")
        
        # Save conversation with UTC datetime for MongoDB TTL index
        await insert_conversation({
            "session_id": request.session_id,
            "question": request.message,
            "answer": answer,
            "timestamp": datetime.now(timezone.utc)
        })
        
        return ChatResponse(answer=answer, data=result.get("db_results"))
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

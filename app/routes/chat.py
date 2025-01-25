from fastapi import APIRouter, HTTPException, Depends
from app.services.session_service import SessionService
from app.services.chat_service import ChatService
from app.models.session import Message, UserSession
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

chat_service = ChatService()


# Request models
class ChatMessage(BaseModel):
    message: str

def get_session(session_id: str) -> UserSession:
    """Dependency to get and validate session"""
    session = SessionService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/session")
async def create_session() -> UserSession:
    """Create a new user session"""
    return SessionService.create_session()

@router.get("/session/{session_id}")
async def get_session_status(session: UserSession = Depends(get_session)) -> UserSession:
    """Get session status and progress"""
    return session

@router.post("/session/{session_id}/advance")
async def advance_to_next_wagon(session: UserSession = Depends(get_session)) -> dict:
    """Advance to the next wagon"""
    success = SessionService.advance_wagon(session.session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot advance to next wagon")
    return {"message": "Advanced to next wagon", "current_wagon": session.current_wagon.wagon_id}

@router.post("/session/{session_id}/{uid}")
async def chat_with_character(
    uid: str,
    # When inheriting from BaseModel, the request body is automatically validated
    chat_message: ChatMessage,
    session: UserSession = Depends(get_session)
) -> dict:
    """Send a message to a character and get their response"""
    # Validate uid format
    try:
        # You need to be in the wagon to chat with the player
        wagon_id = int(uid.split('-')[1])
        if wagon_id != session.current_wagon.wagon_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot chat with character from different wagon"
            )
    except (IndexError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid UID format"
        )

    # Add user message to conversation
    user_message = Message(role="user", content=chat_message.message)
    conversation = SessionService.add_message(session.session_id, uid, user_message)
    
    if not conversation:
        raise HTTPException(
            status_code=500,
            detail="Failed to process message"
        )

    # Generate AI response
    ai_response = chat_service.generate_response(uid, conversation)
    if not ai_response:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response"
        )

    # Add AI response to conversation
    ai_message = Message(role="assistant", content=ai_response)
    SessionService.add_message(session.session_id, uid, ai_message)

    return {
        "uid": uid,
        "response": ai_response,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/session/{session_id}/{uid}/history")
async def get_chat_history(
    uid: str,
    session: UserSession = Depends(get_session)
) -> dict:
    """Get the chat history with a specific character"""
    conversation = SessionService.get_conversation(session.session_id, uid)
    if not conversation:
        return {"uid": uid, "messages": []}
    
    return {
        "uid": uid,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in conversation.messages
        ]
    }

@router.delete("/session/{session_id}")
async def terminate_session(session: UserSession = Depends(get_session)) -> dict:
    """Terminate a chat session and clean up resources"""
    try:
        SessionService.terminate_session(session.session_id)
        return {
            "message": "Session terminated successfully",
            "session_id": session.session_id,
            "terminated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to terminate session: {str(e)}"
        ) 
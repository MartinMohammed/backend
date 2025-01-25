from fastapi import APIRouter, HTTPException, Depends
from app.services.session_service import SessionService
from app.services.chat_service import ChatService
from app.services.guess_service import GuessingService
from app.models.session import Message, UserSession
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
)

# Response models
class GuessResponse(BaseModel):
    guess: str
    thoughts: str
    timestamp: str

class ChatResponse(BaseModel):
    uid: str
    response: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    uid: str
    messages: list[dict]

# Request models
class ChatMessage(BaseModel):
    message: str
    theme: str
    previous_guesses: list[str]
    previous_indications: list[str]
    current_indication: str

# Dependency injection for services
def get_chat_service():
    return ChatService()

def get_guess_service():
    return GuessingService()

def get_session(session_id: str) -> UserSession:
    """Dependency to get and validate session"""
    session = SessionService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/session")
async def create_session() -> UserSession:
    """Create a new user session"""
    session = SessionService.create_session()
    logger.info(f"New session created: {session.session_id}")
    return session

@router.get("/session/{session_id}")
async def get_session_status(
    session: UserSession = Depends(get_session),
) -> UserSession:
    """Get session status and progress"""
    return session

@router.post("/session/{session_id}/advance")
async def advance_to_next_wagon(session: UserSession = Depends(get_session)) -> dict:
    """Advance to the next wagon"""
    success = SessionService.advance_wagon(session.session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot advance to next wagon")
    return {
        "message": "Advanced to next wagon",
        "current_wagon": session.current_wagon.wagon_id,
    }

@router.post("/session/{session_id}/guess", response_model=GuessResponse)
async def guess_password(
    chat_message: ChatMessage,
    session: UserSession = Depends(get_session),
    guess_service: GuessingService = Depends(get_guess_service),
) -> dict:
    guessing_progress = SessionService.get_guessing_progress(session.session_id)

    guess_response = guess_service.generate(
        previous_guesses=guessing_progress.guesses,
        theme="A business of Gold",
        previous_indications=guessing_progress.indications,
        current_indication=chat_message.message,
    )

    SessionService.update_guessing_progress(
        session.session_id,
        chat_message.message,
        guess_response.guess,
        guess_response.thoughts,
    )

    return GuessResponse(
        guess=guess_response.guess,
        thoughts=guess_response.thoughts,
        timestamp=datetime.utcnow().isoformat(),
    )

@router.post("/session/{session_id}/{uid}", response_model=ChatResponse)
async def chat_with_character(
    uid: str,
    chat_message: ChatMessage,
    session: UserSession = Depends(get_session),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict:
    """
    Send a message to a character and get their response.
    The input is a JSON containing the prompt and related data.
    """
    try:
        wagon_id = int(uid.split("-")[1])
        if wagon_id != session.current_wagon.wagon_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot chat with character from different wagon",
            )
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid UID format")

    # Add user message to conversation
    user_message = Message(role="user", content=chat_message.message)
    conversation = SessionService.add_message(session.session_id, uid, user_message)

    if not conversation:
        raise HTTPException(status_code=500, detail="Failed to process message")

    # Generate AI response using the prompt
    character = chat_service._get_character_context(uid)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    system_prompt = chat_service._create_character_prompt(character)
    full_prompt = f"{system_prompt}\n\n{chat_message.message}"

    ai_response = chat_service.generate_response(uid, conversation.messages, full_prompt)
    if not ai_response:
        raise HTTPException(status_code=500, detail="Failed to generate response")

    # Add AI response to conversation
    ai_message = Message(role="assistant", content=ai_response)
    SessionService.add_message(session.session_id, uid, ai_message)

    return {
        "uid": uid,
        "response": ai_response,
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/session/{session_id}/{uid}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    uid: str, session: UserSession = Depends(get_session)
) -> dict:
    conversation = SessionService.get_conversation(session.session_id, uid)
    if not conversation:
        return {"uid": uid, "messages": []}

    return {
        "uid": uid,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in conversation.messages
        ],
    }

@router.delete("/session/{session_id}")
async def terminate_session(session: UserSession = Depends(get_session)) -> dict:
    """Terminate a chat session and clean up resources"""
    try:
        SessionService.terminate_session(session.session_id)
        return {
            "message": "Session terminated successfully",
            "session_id": session.session_id,
            "terminated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to terminate session: {str(e)}"
        )
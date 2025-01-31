from fastapi import APIRouter, HTTPException, Depends
from app.services.session_service import SessionService
from app.services.chat_service import ChatService
from app.services.guess_service import GuessingService
from app.services.scoring_service import ScoringService
from app.services.tts_service import TTSService
from app.models.session import Message, UserSession
from datetime import datetime
from pydantic import BaseModel
import base64
import logging


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatResponse(BaseModel):
    uid: str
    response: str
    audio: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    uid: str
    messages: list[dict]


class GuessResponse(BaseModel):
    guess: str
    thoughts: str
    timestamp: str
    score: float


def get_guess_service():
    return GuessingService()


def get_tts_service():
    return TTSService()


def get_scoring_service():
    return ScoringService()


# Request models
class ChatMessage(BaseModel):
    message: str


def get_session(session_id: str) -> UserSession:
    """Dependency to get and validate session"""
    session = SessionService.get_session(session_id)
    logger.info(f"Session found: {session}")
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


# Add depedency injection and response models
@router.post("/session/{session_id}/guess", response_model=GuessResponse)
async def guess_password(
    chat_message: ChatMessage,
    session: UserSession = Depends(get_session),
    score_service: ScoringService = Depends(get_scoring_service),
    guess_service: GuessingService = Depends(get_guess_service),
) -> dict:
    guessing_progress = SessionService.get_guessing_progress(session.session_id)

    theme = session.current_wagon.theme
    password = session.current_wagon.password

    guess_response = guess_service.generate(
        previous_guesses=guessing_progress.guesses,
        theme=theme,
        previous_indications=guessing_progress.indications,
        current_indication=chat_message.message,
        password=password,
    )

    score = score_service.is_similar(
        password=password, guess=guess_response.guess, theme=password
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
        score=score,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/session/{session_id}/{uid}", response_model=ChatResponse)
async def chat_with_character(
    uid: str,
    chat_message: ChatMessage,
    session: UserSession = Depends(get_session),
    tts_service: TTSService = Depends(get_tts_service),
) -> dict:
    """
    Send a message to a character and get their response.
    The input is a JSON containing the prompt and related data.
    """

    # Get the chat service, that loads the character details
    chat_service = ChatService(session)

    # add first checks that the user exists 
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

    ai_response = chat_service.generate_response(uid, session.current_wagon.theme, conversation)
    if not ai_response:
        raise HTTPException(status_code=500, detail="Failed to generate response")

    # Generate audio from the response
    try:
        audio_bytes = tts_service.convert_text_to_speech(ai_response)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to generate audio: {str(e)}")
        # Continue with text response even if audio fails
        audio_base64 = ""

    # Add AI response to conversation
    ai_message = Message(role="assistant", content=ai_response)
    SessionService.add_message(session.session_id, uid, ai_message)

    return {
        "uid": uid,
        "response": ai_response,
        "audio": audio_base64,
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

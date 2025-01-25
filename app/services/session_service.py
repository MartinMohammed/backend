from datetime import datetime
from typing import Dict, Optional
from app.models.session import UserSession, WagonProgress, Conversation, Message
from app.core.logging import LoggerMixin
import json
from pathlib import Path

class SessionService(LoggerMixin):
    _sessions: Dict[str, UserSession] = {}

    @classmethod
    def create_session(cls) -> UserSession:
        """Create a new user session"""
        session = UserSession()
        # Initialize first wagon
        session.wagons[0] = WagonProgress(wagon_id=0, unlocked=True)
        cls._sessions[session.session_id] = session
        cls.get_logger().info("Created new session", extra={"session_id": session.session_id})
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[UserSession]:
        """Get an existing session by ID"""
        session = cls._sessions.get(session_id)
        if session:
            cls.get_logger().debug("Retrieved session", extra={"session_id": session_id})
        else:
            cls.get_logger().warning("Session not found", extra={"session_id": session_id})
        return session

    @classmethod
    def update_session(cls, session: UserSession) -> None:
        """Update a session's last active timestamp"""
        session.last_active = datetime.utcnow()
        cls._sessions[session.session_id] = session
        cls.get_logger().debug("Updated session", extra={
            "session_id": session.session_id,
            "current_wagon": session.current_wagon_id
        })

    @classmethod
    def add_message(cls, session_id: str, uid: str, message: Message) -> Optional[Conversation]:
        """Add a message to a character's conversation"""
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error("Failed to add message - session not found", extra={
                "session_id": session_id,
                "uid": uid
            })
            return None

        wagon_id = int(uid.split('-')[1])
        if wagon_id not in session.wagons:
            cls.get_logger().info("Initializing new wagon", extra={
                "session_id": session_id,
                "wagon_id": wagon_id
            })
            session.wagons[wagon_id] = WagonProgress(wagon_id=wagon_id, unlocked=True)

        wagon_progress = session.wagons[wagon_id]
        if uid not in wagon_progress.conversations:
            cls.get_logger().info("Starting new conversation", extra={
                "session_id": session_id,
                "uid": uid,
                "wagon_id": wagon_id
            })
            wagon_progress.conversations[uid] = Conversation(uid=uid)

        conversation = wagon_progress.conversations[uid]
        conversation.messages.append(message)
        conversation.last_interaction = datetime.utcnow()
        
        cls.update_session(session)
        cls.get_logger().debug("Added message to conversation", extra={
            "session_id": session_id,
            "uid": uid,
            "message_role": message.role,
            "message_length": len(message.content)
        })
        return conversation

    @classmethod
    def get_conversation(cls, session_id: str, uid: str) -> Optional[Conversation]:
        """Get a conversation with a specific character"""
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error("Failed to get conversation - session not found", extra={
                "session_id": session_id,
                "uid": uid
            })
            return None

        wagon_id = int(uid.split('-')[1])
        if wagon_id not in session.wagons:
            cls.get_logger().warning("Wagon not found in session", extra={
                "session_id": session_id,
                "wagon_id": wagon_id
            })
            return None

        conversation = session.wagons[wagon_id].conversations.get(uid)
        if conversation:
            cls.get_logger().debug("Retrieved conversation", extra={
                "session_id": session_id,
                "uid": uid,
                "message_count": len(conversation.messages)
            })
        else:
            cls.get_logger().debug("No conversation found", extra={
                "session_id": session_id,
                "uid": uid
            })
        return conversation

    @classmethod
    def advance_wagon(cls, session_id: str) -> bool:
        """Advance to the next wagon and clear previous conversations"""
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error("Failed to advance wagon - session not found", extra={
                "session_id": session_id
            })
            return False

        wagons_file = Path("data/wagons.json")
        try:
            with open(wagons_file, "r") as f:
                wagons_data = json.load(f)
                max_wagon_id = len(wagons_data["wagons"]) - 1
        except Exception as e:
            cls.get_logger().error("Failed to read wagons data", extra={
                "session_id": session_id,
                "error": str(e)
            })
            return False

        next_wagon_id = session.current_wagon_id + 1
        if next_wagon_id > max_wagon_id:
            cls.get_logger().warning("Cannot advance - already at last wagon", extra={
                "session_id": session_id,
                "current_wagon": session.current_wagon_id
            })
            return False

        if session.current_wagon_id in session.wagons:
            del session.wagons[session.current_wagon_id]
            cls.get_logger().info("Cleared previous wagon data", extra={
                "session_id": session_id,
                "cleared_wagon": session.current_wagon_id
            })

        session.current_wagon_id = next_wagon_id
        session.wagons[next_wagon_id] = WagonProgress(wagon_id=next_wagon_id, unlocked=True)
        cls.update_session(session)
        
        cls.get_logger().info("Advanced to next wagon", extra={
            "session_id": session_id,
            "new_wagon": next_wagon_id
        })
        return True

    @classmethod
    def cleanup_old_sessions(cls, max_age_hours: int = 24) -> None:
        """Remove sessions older than specified hours"""
        current_time = datetime.utcnow()
        sessions_to_remove = []
        
        for session_id, session in cls._sessions.items():
            age = (current_time - session.last_active).total_seconds() / 3600
            if age > max_age_hours:
                sessions_to_remove.append(session_id)
                cls.get_logger().info("Marking session for cleanup", extra={
                    "session_id": session_id,
                    "age_hours": age
                })
        
        for session_id in sessions_to_remove:
            del cls._sessions[session_id]
            cls.get_logger().info("Cleaned up old session", extra={
                "session_id": session_id
            }) 
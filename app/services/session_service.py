from datetime import datetime
from typing import Dict, Optional
from app.models.session import (
    UserSession,
    WagonProgress,
    Conversation,
    Message,
    GuessingProgress,
)
from app.core.logging import LoggerMixin
import json
from pathlib import Path


# used as dependency injection for the session service
class SessionService(LoggerMixin):
    # dictionary to store all the sessions
    _sessions: Dict[str, UserSession] = {}

    @classmethod
    def create_session(cls) -> UserSession:
        """Create a new user session"""
        # create a new session and store it in the dictionary
        session = UserSession()
        cls._sessions[session.session_id] = session
        cls.get_logger().info(
            "Created new session", extra={"session_id": session.session_id}
        )
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[UserSession]:
        """Get an existing session by ID"""
        # get the session from the dictionary
        session = cls._sessions.get(session_id)

        if session:
            cls.get_logger().debug(
                "Retrieved session", extra={"session_id": session_id}
            )
        else:
            cls.get_logger().warning(
                "Session not found", extra={"session_id": session_id}
            )
        return session

    @classmethod
    def update_session(cls, session: UserSession) -> None:
        """Update a session's last active timestamp"""
        # update the last active timestamp
        session.last_active = datetime.utcnow()
        # update the session in the dictionary by overriding the existing session
        cls._sessions[session.session_id] = session
        cls.get_logger().debug(
            "Updated session",
            extra={
                "session_id": session.session_id,
                "current_wagon": session.current_wagon.wagon_id,
            },
        )

    @classmethod
    def add_message(
        cls, session_id: str, uid: str, message: Message
    ) -> Optional[Conversation]:
        """Add a message to a character's conversation"""
        # get the session from the dictionary
        session = cls.get_session(session_id)
        # check if the session exists
        if not session:
            cls.get_logger().error(
                "Failed to add message - session not found",
                extra={"session_id": session_id, "uid": uid},
            )
            return None

        # get the wagon id from the uid
        # uuid is in the format of wagon-<i>-player-<k>
        wagon_id = int(uid.split("-")[1])
        # check if the wagon id is the same as the current wagon id
        # if the wagon id is not the same, client is trying to access a different wagon
        # which might indicate out of sync in wagon.
        if wagon_id != session.current_wagon.wagon_id:
            cls.get_logger().error(
                "Cannot add message - wrong wagon",
                extra={
                    "session_id": session_id,
                    "uid": uid,
                    "current_wagon": session.current_wagon.wagon_id,
                },
            )
            return None

        # in case we have not started a conversation with this character yet, start one
        if uid not in session.current_wagon.conversations:
            cls.get_logger().info(
                "Starting new conversation",
                extra={"session_id": session_id, "uid": uid, "wagon_id": wagon_id},
            )
            session.current_wagon.conversations[uid] = Conversation(uid=uid)

        # add the message of the client to the conversation with the new player
        conversation = session.current_wagon.conversations[uid]
        conversation.messages.append(message)
        conversation.last_interaction = datetime.utcnow()

        cls.update_session(session)
        cls.get_logger().debug(
            "Added message to conversation",
            extra={
                "session_id": session_id,
                "uid": uid,
                "message_role": message.role,
                "message_length": len(message.content),
            },
        )
        return conversation

    @classmethod
    def get_conversation(cls, session_id: str, uid: str) -> Optional[Conversation]:
        """Get a conversation with a specific character"""
        session = cls.get_session(session_id)
        # check if the session exists
        if not session:
            cls.get_logger().error(
                "Failed to get conversation - session not found",
                extra={"session_id": session_id, "uid": uid},
            )
            return None

        # get the wagon id from the uid
        # uuid is in the format of wagon-<i>-player-<k>
        wagon_id = int(uid.split("-")[1])
        # check if the wagon id is the same as the current wagon id
        # if the wagon id is not the same, client is trying to access a different wagon
        # which might indicate out of sync in wagon.
        if wagon_id != session.current_wagon.wagon_id:
            cls.get_logger().warning(
                "Cannot get conversation - wrong wagon",
                extra={
                    "session_id": session_id,
                    "uid": uid,
                    "current_wagon": session.current_wagon.wagon_id,
                },
            )
            return None

        # get the conversation from the current wagon
        conversation = session.current_wagon.conversations.get(uid)

        if conversation:
            cls.get_logger().debug(
                "Retrieved conversation",
                extra={
                    "session_id": session_id,
                    "uid": uid,
                    "message_count": len(conversation.messages),
                },
            )
        else:
            cls.get_logger().debug(
                "No conversation found", extra={"session_id": session_id, "uid": uid}
            )
        return conversation

    @classmethod
    def get_guessing_progress(cls, session_id: str) -> GuessingProgress:
        session = cls.get_session(session_id)

        if not session:
            cls.get_logger().error(
                "Failed to get guesses - session not found",
                extra={"session_id": session_id},
            )
            return

        return session.guessing_progress

    @classmethod
    def update_guessing_progress(
<<<<<<< HEAD
        cls, session_id: str, indication: str, guess: str
=======
        cls, session_id: str, indication: str, guess: str, thought: list[str]
>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
    ) -> None:
        session = cls.get_session(session_id)

        if not session:
            cls.get_logger().error(
                "Failed to get the guessing progress - session not found",
                extra={"session_id": session_id},
            )
            return

        session.guessing_progress.guesses.append(guess)
        session.guessing_progress.indications.append(
            Message(
                role="user",
                content=indication,
            )
        )

<<<<<<< HEAD
=======
        if session.current_wagon.conversations.get("main-character") is None:
            session.current_wagon.conversations["main-character"] = Conversation(
                uid="main-character"
            )

        
        messages = session.current_wagon.conversations.get("main-character").messages
        messages.append(
            Message(role="user", content=indication)
        )
        messages.append(
            Message(role="assistant", content=thought[0])
        )

>>>>>>> 83ed757c1e333edd6dbaa922dc6fe7e43c254687
        cls.update_session(session)
        cls.get_logger().info(
            "Added a new guess",
            extra={"session_id": session_id},
        )

    @classmethod
    def advance_wagon(cls, session_id: str) -> bool:
        """Advance to the next wagon"""
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error(
                "Failed to advance wagon - session not found",
                extra={"session_id": session_id},
            )
            return False

        wagons_file = Path("data/wagons.json")
        try:
            with open(wagons_file, "r") as f:
                wagons_data = json.load(f)
                # we start counting from 0, max_wagon_id is the last wagon id
                max_wagon_id = len(wagons_data["wagons"]) - 1
        except Exception as e:
            cls.get_logger().error(
                "Failed to read wagons data",
                extra={"session_id": session_id, "error": str(e)},
            )
            return False

        # advance to the next wagon
        next_wagon_id = session.current_wagon.wagon_id + 1
        # check if we are out of bounds
        if next_wagon_id > max_wagon_id:
            cls.get_logger().warning(
                "Cannot advance - already at last wagon",
                extra={
                    "session_id": session_id,
                    "current_wagon": session.current_wagon.wagon_id,
                },
            )
            return False

        # Set up next wagon
        session.current_wagon = WagonProgress(wagon_id=next_wagon_id)

        # Clean up the previous guesses
        session.current_guesses = GuessingProgress()
        cls.update_session(session)

        cls.get_logger().info(
            "Advanced to next wagon",
            extra={"session_id": session_id, "new_wagon": next_wagon_id},
        )
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
                cls.get_logger().info(
                    "Marking session for cleanup",
                    extra={"session_id": session_id, "age_hours": age},
                )

        for session_id in sessions_to_remove:
            del cls._sessions[session_id]
            cls.get_logger().info(
                "Cleaned up old session", extra={"session_id": session_id}
            )

    @classmethod
    def terminate_session(cls, session_id: str) -> None:
        """Terminate a session and clean up its resources"""
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().warning(
                "Attempted to terminate non-existent session",
                extra={"session_id": session_id},
            )
            return

        # Clean up session data
        if session_id in cls._sessions:
            del cls._sessions[session_id]
            cls.get_logger().info(
                "Session terminated",
                extra={
                    "session_id": session_id,
                    "terminated_at": datetime.utcnow().isoformat(),
                    "final_wagon": session.current_wagon.wagon_id,
                },
            )

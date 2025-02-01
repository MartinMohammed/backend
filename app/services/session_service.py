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
import uuid
from app.utils.file_management import FileManager


# used as dependency injection for the session service
class SessionService(LoggerMixin):
    # dictionary to store all the sessions
    _sessions: Dict[str, UserSession] = {}

    @classmethod
    def create_session(cls) -> UserSession:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        session = UserSession(
            session_id=session_id,
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            default_game=True
        )
        
        cls._sessions[session_id] = session
        cls.get_logger().info(f"Created new session: {session_id}")
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = cls._sessions.get(session_id)
        if session:
            session.last_active = datetime.utcnow()
            cls.get_logger().debug(f"Retrieved session: {session_id}")
        else:
            cls.get_logger().warning(f"Session not found: {session_id}")
        return session

    @classmethod
    def update_session(cls, session: UserSession) -> None:
        """Update a session's last active timestamp"""
        session.last_active = datetime.utcnow()
        cls._sessions[session.session_id] = session
        cls.get_logger().debug(
            f"Updated session | session_id: {session.session_id} | current_wagon: {session.current_wagon.wagon_id}"
        )

    @classmethod
    def add_message(
        cls, session_id: str, uid: str, message: Message
    ) -> Optional[Conversation]:
        """Add a message to a character's conversation"""
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error(
                f"Failed to add message - session not found | session_id: {session_id} | uid: {uid}"
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
                f"Cannot add message - wrong wagon | session_id: {session_id} | uid: {uid} | current_wagon: {session.current_wagon.wagon_id}"
            )
            return None

        # in case we have not started a conversation with this character yet, start one
        if uid not in session.current_wagon.conversations:
            cls.get_logger().info(
                f"Starting new conversation | session_id: {session_id} | uid: {uid} | wagon_id: {wagon_id}"
            )
            session.current_wagon.conversations[uid] = Conversation(uid=uid)

        # add the message of the client to the conversation with the new player
        conversation = session.current_wagon.conversations[uid]
        conversation.messages.append(message)
        conversation.last_interaction = datetime.utcnow()

        cls.update_session(session)
        cls.get_logger().debug(
            f"Added message to conversation | session_id: {session_id} | uid: {uid} | message_role: {message.role} | message_length: {len(message.content)}"
        )
        return conversation

    @classmethod
    def get_conversation(cls, session_id: str, uid: str) -> Optional[Conversation]:
        """Get a conversation with a specific character"""
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error(
                f"Failed to get conversation - session not found | session_id: {session_id} | uid: {uid}"
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
                f"Cannot get conversation - wrong wagon | session_id: {session_id} | uid: {uid} | current_wagon: {session.current_wagon.wagon_id}"
            )
            return None

        # get the conversation from the current wagon
        conversation = session.current_wagon.conversations.get(uid)

        if conversation:
            cls.get_logger().debug(
                f"Retrieved conversation | session_id: {session_id} | uid: {uid} | message_count: {len(conversation.messages)}"
            )
        else:
            cls.get_logger().debug(
                f"No conversation found | session_id: {session_id} | uid: {uid}"
            )
        return conversation

    @classmethod
    def get_guessing_progress(cls, session_id: str) -> GuessingProgress:
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error(
                f"Failed to get guesses - session not found | session_id: {session_id}"
            )
            return None
        return session.guessing_progress

    @classmethod
    def update_guessing_progress(
        cls, session_id: str, indication: str, guess: str, thought: list[str]
    ) -> None:
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error(
                f"Failed to get the guessing progress - session not found | session_id: {session_id}"
            )
            return

        session.guessing_progress.guesses.append(guess)
        session.guessing_progress.indications.append(
            Message(
                role="user",
                content=indication,
            )
        )

        wagon_id = session.current_wagon.wagon_id

        if (
            session.current_wagon.conversations.get(f"wagon-{wagon_id}-player-0")
            is None
        ):
            session.current_wagon.conversations[f"wagon-{wagon_id}-player-0"] = (
                Conversation(uid="player-0")
            )

        messages = session.current_wagon.conversations.get(
            f"wagon-{wagon_id}-player-0"
        ).messages

        messages.append(Message(role="user", content=indication))
        messages.append(Message(role="assistant", content=thought[0]))

        cls.update_session(session)
        cls.get_logger().info(f"Added a new guess | session_id: {session_id}")

    @classmethod
    def advance_wagon(cls, session_id: str) -> bool:
        """Advance to the next wagon"""
        cls.get_logger().info(f"Attempting to advance wagon | session_id={session_id}")
        
        # Get current session
        session = cls.get_session(session_id)
        if not session:
            cls.get_logger().error(f"Failed to advance wagon - session not found | session_id={session_id}")
            return False

        current_wagon_id = session.current_wagon.wagon_id
        cls.get_logger().debug(f"Current wagon state | session_id={session_id} | current_wagon_id={current_wagon_id}")

        try: 
            # Load data based on default_game flag
            cls.get_logger().debug(f"Loading session data | session_id={session_id} | default_game={session.default_game}")
            next_wagon_id = current_wagon_id + 1
            _, _, wagons = FileManager.load_session_data(session_id, session.default_game)
            max_wagons = len(wagons)

             # Check if we're at the last wagon
            if next_wagon_id > max_wagons - 1:
                cls.get_logger().warning(
                    f"Cannot advance - already at last wagon | session_id={session_id} | current_wagon={current_wagon_id} | max_wagons={max_wagons}"
                )
                raise Exception("Cannot advance - already at last wagon")
            
            cls.get_logger().debug(
                f"Wagon progression details | session_id={session_id} | current_wagon={current_wagon_id} | next_wagon={next_wagon_id} | max_wagons={max_wagons}"
            )

            # Load current wagon data for the next wagon setup
            current_wagon = wagons[next_wagon_id]
            
            # Set up next wagon
            session.current_wagon = WagonProgress(
                wagon_id=next_wagon_id,
                theme=current_wagon["theme"],
                password=current_wagon["passcode"],
            )

            # Reset guessing progress for new wagon
            session.guessing_progress = GuessingProgress()
            cls.update_session(session)

            cls.get_logger().info(
                f"Successfully advanced to next wagon | session_id={session_id} | previous_wagon={current_wagon_id} | new_wagon={next_wagon_id} | theme={current_wagon['theme']}"
            )
            return True

        except FileNotFoundError as e:
            cls.get_logger().error(
                f"Failed to load session data | session_id={session_id} | error={str(e)} | error_type=FileNotFoundError"
            )
            return False
        except KeyError as e:
            cls.get_logger().error(
                f"Invalid wagon data structure | session_id={session_id} | error={str(e)} | error_type=KeyError"
            )
            return False
        except Exception as e:
            cls.get_logger().error(
                f"Unexpected error during wagon advancement | session_id={session_id} | error={str(e)} | error_type={type(e).__name__}"
            )
            return False

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
                    f"Marking session for cleanup | session_id: {session_id} | age_hours: {age}"
                )

        for session_id in sessions_to_remove:
            cls.terminate_session(session_id)
            cls.get_logger().info(f"Cleaned up old session | session_id: {session_id}")

    @classmethod
    def terminate_session(cls, session_id: str) -> None:
        """Terminate a session and clean up its resources"""
        if session_id in cls._sessions:
            del cls._sessions[session_id]
            cls.get_logger().info(f"Terminated session: {session_id}")

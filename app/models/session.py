from pydantic import BaseModel, Field
from typing import Dict, List, Literal
from datetime import datetime
import uuid


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    uid: str
    messages: List[Message] = Field(default_factory=list)
    last_interaction: datetime = Field(default_factory=datetime.utcnow)


class GuessingProgress(BaseModel):
    indications: list[Message] = Field(default_factory=list)
    guesses: list[str] = Field(default_factory=list)


class WagonProgress(BaseModel):
    wagon_id: int = 0
    conversations: Dict[str, Conversation] = Field(default_factory=dict)


class UserSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_wagon: WagonProgress = Field(default_factory=WagonProgress)
    guessing_progress: GuessingProgress = Field(default_factory=GuessingProgress)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_wagon": {"wagon_id": 0, "conversations": {}},
            }
        }

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseModel):
    uid: str
    messages: List[Message] = Field(default_factory=list)
    last_interaction: datetime = Field(default_factory=datetime.utcnow)

class WagonProgress(BaseModel):
    wagon_id: int
    conversations: Dict[str, Conversation] = Field(default_factory=dict)
    completed: bool = False
    unlocked: bool = False
    passcode: Optional[str] = None

class UserSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_wagon_id: int = 0
    wagons: Dict[int, WagonProgress] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_wagon_id": 0,
                "wagons": {
                    "0": {
                        "wagon_id": 0,
                        "conversations": {},
                        "completed": False,
                        "unlocked": True
                    }
                }
            }
        } 
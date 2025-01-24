from pydantic import BaseModel
from typing import Literal


class State(BaseModel):
    user_id: str
    conversation_id: str
    question: str
    response: str
    hint: str
    status: Literal["Ongoing", "Finished"]

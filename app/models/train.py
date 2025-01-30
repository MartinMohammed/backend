from pydantic import BaseModel, Field
from typing import List, Dict

class PassengerProfile(BaseModel):
    name: str
    age: int
    profession: str
    personality: str
    role: str
    mystery_intrigue: str

class PlayerName(BaseModel):
    firstName: str
    lastName: str
    sex: str
    fullName: str

class PlayerDetails(BaseModel):
    profile: PassengerProfile

class Person(BaseModel):
    uid: str
    position: List[float] = Field(..., min_items=2, max_items=2)
    rotation: float
    model_type: str
    items: List[str] = []

class Wagon(BaseModel):
    id: int
    theme: str
    passcode: str
    people: List[Person]

class Names(BaseModel):
    names: Dict[str, Dict[str, PlayerName]]

class PlayerDetailsResponse(BaseModel):
    player_details: Dict[str, Dict[str, PlayerDetails]]

class WagonsResponse(BaseModel):
    wagons: List[Wagon]

class GenerateTrainResponse(BaseModel):
    names: Names
    player_details: PlayerDetailsResponse
    wagons: WagonsResponse 
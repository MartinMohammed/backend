from pydantic import BaseModel, Field
from typing import List

class PassengerProfile(BaseModel):
    name: str
    age: int
    profession: str
    personality: str
    role: str
    mystery_intrigue: str

class PlayerName(BaseModel):
    playerId: str
    firstName: str
    lastName: str
    sex: str
    fullName: str

class PlayerDetails(BaseModel):
    playerId: str
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

class WagonNames(BaseModel):
    wagonId: str
    players: List[PlayerName]

class WagonPlayerDetails(BaseModel):
    wagonId: str
    players: List[PlayerDetails]


class WagonsResponse(BaseModel):
    wagons: List[Wagon]

class GenerateTrainResponse(BaseModel):
    names: List[WagonNames]
    player_details: List[WagonPlayerDetails]
    wagons: List[Wagon]
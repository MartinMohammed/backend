from fastapi import APIRouter, HTTPException, Query, status, Path
from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel, Field, create_model
import json
from pathlib import Path as PathLib
from app.core.logging import get_logger

# Base Response Models
class NameInfo(BaseModel):
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Smith")
    nickname: Optional[str] = Field(None, example="Johnny")

class Profile(BaseModel):
    age: int = Field(..., example=25)
    occupation: str = Field(..., example="Merchant")
    background: str = Field(..., example="Former city trader")

def create_player_response_model(properties: Optional[List[str]] = None) -> Type[BaseModel]:
    """Create a dynamic PlayerResponse model based on requested properties"""
    # Base fields that are always included
    fields = {
        "id": (str, Field(..., example="player_123"))
    }
    
    if properties:
        valid_properties = {
            "name_info": (Optional[Dict[str, Any]], Field(None, example={"first_name": "John", "last_name": "Smith"})),
            "profile": (Optional[Dict[str, Any]], Field(None)),
            "traits": (Optional[Dict[str, Any]], Field(None)),
            "inventory": (Optional[Dict[str, Any]], Field(None)),
            "dialogue": (Optional[Dict[str, Any]], Field(None))
        }
        
        for prop in properties:
            if prop in valid_properties:
                fields[prop] = valid_properties[prop]
    
    return create_model("DynamicPlayerResponse", **fields)

def create_players_response_model(properties: Optional[List[str]] = None) -> Type[BaseModel]:
    """Create a dynamic PlayersResponse model based on requested properties"""
    player_model = create_player_response_model(properties)
    return create_model("DynamicPlayersResponse", players=(List[player_model], ...))

router = APIRouter(
    prefix="/players",
    tags=["players"],
    responses={404: {"description": "Not found"}}
)
logger = get_logger("players")

def load_json_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as f:
            logger.debug(f"Loading JSON file: {file_path}")
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {str(e)}")
        return {}

def filter_player_info(complete_info: dict, properties: List[str] = None) -> dict:
    if not properties:
        logger.debug("No properties filter applied")
        return complete_info
    
    filtered_info = {
        "id": complete_info["id"]  # Always include the id field
    }
    valid_properties = {"name_info", "profile", "traits", "inventory", "dialogue"}
    
    logger.info(f"Filtering properties: {properties}")
    for prop in properties:
        if prop in valid_properties and prop in complete_info:
            filtered_info[prop] = complete_info[prop]
        else:
            logger.warning(f"Invalid or missing property requested: {prop}")
    
    return filtered_info

@router.get("/players/{wagon_id}/{player_id}",
    summary="Get single player information",
    description="""
    Retrieve detailed information about a specific player in a wagon.
    
    The response can be filtered to include only specific properties using the query parameter.
    Available properties are: name_info, profile, traits, inventory, dialogue
    """,
    responses={
        200: {
            "description": "Successfully retrieved player information",
            "content": {
                "application/json": {
                    "example": {
                        "players": [{
                            "id": "player_123",
                            "name_info": {"first_name": "John", "last_name": "Smith"},
                            "profile": {"age": 25, "occupation": "Merchant"},
                            "traits": {"charisma": 8, "intelligence": 7},
                            "inventory": {"gold": 100, "items": ["map", "compass"]},
                            "dialogue": {"greeting": "Hello there!"}
                        }]
                    }
                }
            }
        },
        404: {"description": "Player or wagon not found"}
    }
)
async def get_player_info(
    wagon_id: str = Path(..., description="The ID of the wagon"),
    player_id: str = Path(..., description="The ID of the player"),
    properties: Optional[List[str]] = Query(
        None,
        description="Filter specific properties (name_info, profile, traits, inventory, dialogue)",
        example=["name_info", "profile"]
    )
):
    logger.info(f"Getting player info for wagon_id={wagon_id}, player_id={player_id}")
    if properties:
        logger.info(f"Requested properties: {properties}")

    # Create dynamic response model
    response_model = create_players_response_model(properties)
    
    # Define paths to JSON files
    data_dir = PathLib("data")
    player_details_path = data_dir / "player_details.json"
    names_path = data_dir / "names.json"
    
    # Load data from JSON files
    player_details = load_json_file(player_details_path)
    names_data = load_json_file(names_path)
    
    # Get player details
    try:
        player_info = player_details["player_details"][wagon_id][player_id]
        logger.debug(f"Found player details for {player_id} in wagon {wagon_id}")
    except KeyError:
        logger.error(f"Player not found: wagon_id={wagon_id}, player_id={player_id}")
        raise HTTPException(status_code=404, detail="Player not found in player details")
    
    # Get player name information
    try:
        name_info = names_data["names"][wagon_id][player_id]
        logger.debug(f"Found name information for {player_id} in wagon {wagon_id}")
    except KeyError:
        logger.warning(f"Name information not found for player {player_id} in wagon {wagon_id}")
        name_info = {}
    
    # Combine all information
    complete_player_info = {
        "id": player_id,
        "name_info": name_info,
        "profile": player_info.get("profile", {}),
        "traits": player_info.get("traits", {}),
        "inventory": player_info.get("inventory", {}),
        "dialogue": player_info.get("dialogue", {})
    }
    
    # Filter properties if specified
    result = filter_player_info(complete_player_info, properties)
    logger.info(f"Successfully retrieved player info for {player_id} in wagon {wagon_id}")
    
    # Validate response against dynamic model
    return response_model(players=[result])

@router.get("/players/{wagon_id}",
    summary="Get all players in a wagon",
    description="""
    Retrieve information about all players in a specific wagon.
    
    The response can be filtered to include only specific properties using the query parameter.
    Available properties are: name_info, profile, traits, inventory, dialogue
    """,
    responses={
        200: {
            "description": "Successfully retrieved all players in the wagon",
            "content": {
                "application/json": {
                    "example": {
                        "players": [
                            {
                                "id": "player_123",
                                "name_info": {"first_name": "John", "last_name": "Smith"},
                                "profile": {"age": 25, "occupation": "Merchant"}
                            },
                            {
                                "id": "player_124",
                                "name_info": {"first_name": "Jane", "last_name": "Doe"},
                                "profile": {"age": 28, "occupation": "Doctor"}
                            }
                        ]
                    }
                }
            }
        },
        404: {"description": "Wagon not found"}
    }
)
async def get_wagon_players(
    wagon_id: str = Path(..., description="The ID of the wagon"),
    properties: Optional[List[str]] = Query(
        None,
        description="Filter specific properties (name_info, profile, traits, inventory, dialogue)",
        example=["name_info", "profile"]
    )
):
    logger.info(f"Getting all players for wagon_id={wagon_id}")
    if properties:
        logger.info(f"Requested properties: {properties}")

    # Create dynamic response model
    response_model = create_players_response_model(properties)
    
    # Define paths to JSON files
    data_dir = PathLib("data")
    player_details_path = data_dir / "player_details.json"
    names_path = data_dir / "names.json"
    
    # Load data from JSON files
    player_details = load_json_file(player_details_path)
    names_data = load_json_file(names_path)
    
    try:
        wagon_players = player_details["player_details"][wagon_id]
        wagon_names = names_data["names"][wagon_id]
        logger.debug(f"Found {len(wagon_players)} players in wagon {wagon_id}")
        
        # Combine information for all players in the wagon
        players_info = {
            "players": []
        }

        for player_id in wagon_players:
            logger.debug(f"Processing player {player_id} in wagon {wagon_id}")
            complete_info = {
                "id": player_id,  # Ensure id is always included
                "name_info": wagon_names.get(player_id, {}),
                "profile": wagon_players[player_id].get("profile", {}),
                "traits": wagon_players[player_id].get("traits", {}),
                "inventory": wagon_players[player_id].get("inventory", {}),
                "dialogue": wagon_players[player_id].get("dialogue", {})
            }
            filtered_info = filter_player_info(complete_info, properties)
            players_info["players"].append(filtered_info)
        
        logger.info(f"Successfully retrieved all players for wagon {wagon_id}")
        
        # Validate response against dynamic model
        return response_model(players=players_info["players"])
    except KeyError:
        logger.error(f"Wagon not found: wagon_id={wagon_id}")
        raise HTTPException(status_code=404, detail="Wagon not found") 
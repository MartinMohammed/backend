from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
from pathlib import Path
from app.core.logging import get_logger

router = APIRouter()
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
    
    filtered_info = {}
    valid_properties = {"name_info", "profile", "traits", "inventory", "dialogue"}
    
    logger.info(f"Filtering properties: {properties}")
    for prop in properties:
        if prop in valid_properties and prop in complete_info:
            filtered_info[prop] = complete_info[prop]
        else:
            logger.warning(f"Invalid or missing property requested: {prop}")
    
    return filtered_info

@router.get("/api/players/{wagon_id}/{player_id}")
async def get_player_info(
    wagon_id: str, 
    player_id: str,
    properties: Optional[List[str]] = Query(
        None,
        description="Filter specific properties (name_info, profile, traits, inventory, dialogue)"
    )
):
    logger.info(f"Getting player info for wagon_id={wagon_id}, player_id={player_id}")
    if properties:
        logger.info(f"Requested properties: {properties}")

    # Define paths to JSON files
    data_dir = Path("data")
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
        "name_info": name_info,
        "profile": player_info.get("profile", {}),
        "traits": player_info.get("traits", {}),
        "inventory": player_info.get("inventory", {}),
        "dialogue": player_info.get("dialogue", {})
    }
    
    # Filter properties if specified
    result = filter_player_info(complete_player_info, properties)
    logger.info(f"Successfully retrieved player info for {player_id} in wagon {wagon_id}")
    return result

@router.get("/api/players/{wagon_id}")
async def get_wagon_players(
    wagon_id: str,
    properties: Optional[List[str]] = Query(
        None,
        description="Filter specific properties (name_info, profile, traits, inventory, dialogue)"
    )
):
    logger.info(f"Getting all players for wagon_id={wagon_id}")
    if properties:
        logger.info(f"Requested properties: {properties}")

    # Define paths to JSON files
    data_dir = Path("data")
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
        players_info = {}
        for player_id in wagon_players:
            logger.debug(f"Processing player {player_id} in wagon {wagon_id}")
            complete_info = {
                "name_info": wagon_names.get(player_id, {}),
                "profile": wagon_players[player_id].get("profile", {}),
                "traits": wagon_players[player_id].get("traits", {}),
                "inventory": wagon_players[player_id].get("inventory", {}),
                "dialogue": wagon_players[player_id].get("dialogue", {})
            }
            players_info[player_id] = filter_player_info(complete_info, properties)
        
        logger.info(f"Successfully retrieved all players for wagon {wagon_id}")
        return players_info
    except KeyError:
        logger.error(f"Wagon not found: wagon_id={wagon_id}")
        raise HTTPException(status_code=404, detail="Wagon not found") 
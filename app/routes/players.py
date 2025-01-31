from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
from pathlib import Path
from app.core.logging import get_logger
from app.services.session_service import SessionService
from app.utils.file_management import FileManager

router = APIRouter(tags=["players"])

logger = get_logger("players")


def load_json_file(file_path: str) -> dict:
    try:
        with open(file_path, "r") as f:
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
    # Add the id to the filtered info
    filtered_info["id"] = complete_info["id"]
    valid_properties = {"profile", "name_info"}

    logger.info(f"Filtering properties: {properties}")
    for prop in properties:
        if prop in valid_properties and prop in complete_info:
            filtered_info[prop] = complete_info[prop]
        else:
            logger.warning(f"Invalid or missing property requested: {prop}")

    return filtered_info


@router.get("/api/players/{session_id}/{wagon_id}/{player_id}")
async def get_player_info(
    session_id: str,
    wagon_id: str,
    player_id: str,
    properties: Optional[List[str]] = Query(None, description="Filter specific properties")
):
    logger.info(
        f"Getting player info | session_id: {session_id} | wagon_id: {wagon_id} | player_id: {player_id} | requested_properties: {properties}"
    )
    
    try:
        session = SessionService.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
            
        logger.debug(
            f"Loading session data | session_id: {session_id} | default_game: {session.default_game}"
        )
        
        # Load data based on default_game flag
        names, player_details, _ = FileManager.load_session_data(session_id, session.default_game)
        
        try:
            # First check if player_details is contained in the loaded data
            if "player_details" not in player_details:
                logger.error("Missing 'player_details' key in loaded data")
                raise HTTPException(status_code=404, detail="Player details not found")
            
            player_info = player_details["player_details"][wagon_id][player_id]
            logger.debug(
                f"Found player info | wagon: {wagon_id} | player: {player_id} | profile_exists: {'profile' in player_info}"
            )

            # first check if names is contained in the loaded data
            if "names" not in names:
                logger.error("Missing 'names' key in loaded data")
                raise HTTPException(status_code=404, detail="Names not found")
            
            name_info = names["names"][wagon_id][player_id]
            logger.debug(
                f"Found name info | wagon: wagon_id | player: player_id"
            )
            
            # Combine information
            complete_player_info = {
                "id": player_id,
                "name_info": name_info,
                "profile": player_info.get("profile", {})
            }
            
            # Filter properties if specified
            if properties:
                logger.info(
                    f"Filtering player info | requested_properties: {properties} | available_properties: {list(complete_player_info.keys())}"
                )
                return filter_player_info(complete_player_info, properties)
            
            logger.info("Successfully retrieved complete player info")
            return complete_player_info
            
        except KeyError as e:
            logger.error(
                f"Failed to find player data | error: {str(e)} | wagon_id: {wagon_id} | player_id: {player_id}"
            )
            raise HTTPException(status_code=404, detail="Player not found")
            
    except FileNotFoundError as e:
        logger.error(
            f"Failed to load session data | error: {str(e)} | session_id: {session_id}"
        )
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/api/players/{session_id}/{wagon_id}")
async def get_wagon_players(
    session_id: str,
    wagon_id: str,
    properties: Optional[List[str]] = Query(
        None,
        description="Filter specific properties (name_info, profile, traits, inventory, dialogue)",
    ),
):
    session = SessionService.get_session(session_id)
    # check if session is found
    if not session:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    logger.info(f"Getting all players for wagon_id={wagon_id} | session_id={session_id}")
    if properties:
        logger.info(f"Requested properties: {properties}")

    logger.debug(
        f"Loading session data | session_id={session_id} | default_game={session.default_game}"
    )
    
    try:
        # Load data based on default_game flag
        names, player_details, _ = FileManager.load_session_data(session_id, session.default_game)
        
        # First check if player_details is contained in the loaded data
        if "player_details" not in player_details:
            logger.error("Missing 'player_details' key in loaded data")
            raise HTTPException(status_code=404, detail="Player details not found")
        
        # Check if wagon exists in player_details
        if wagon_id not in player_details["player_details"]:
            logger.error(f"Wagon not found | wagon_id={wagon_id}")
            raise HTTPException(status_code=404, detail="Wagon not found")
            
        player_info = player_details["player_details"][wagon_id]
        logger.debug(f"Found player info | wagon={wagon_id} | player_count={len(player_info)}")

        # Check if names data exists and is valid
        if "names" not in names:
            logger.error("Missing 'names' key in loaded data")
            raise HTTPException(status_code=404, detail="Names not found")
            
        if wagon_id not in names["names"]:
            logger.error(f"Wagon names not found | wagon_id={wagon_id}")
            raise HTTPException(status_code=404, detail="Wagon names not found")
            
        name_info = names["names"][wagon_id]
        logger.debug(f"Found name info | wagon={wagon_id} | name_count={len(name_info)}")
            
        # Combine information for all players in the wagon
        players_info = []
        for player_id in player_info:
            logger.debug(f"Processing player | wagon={wagon_id} | player={player_id}")
            complete_info = {
                "id": player_id,
                "name_info": name_info.get(player_id, {}),
                "profile": player_info[player_id].get("profile", {})
            }
            filtered_info = filter_player_info(complete_info, properties)
            players_info.append(filtered_info)

        logger.info(f"Successfully retrieved all players | wagon={wagon_id} | player_count={len(players_info)}")
        return {"players": players_info}
            
    except FileNotFoundError as e:
        logger.error(f"Failed to load session data | error={str(e)} | session_id={session_id}")
        raise HTTPException(status_code=404, detail="Session data not found")
    except Exception as e:
        logger.error(f"Unexpected error | error={str(e)} | wagon_id={wagon_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

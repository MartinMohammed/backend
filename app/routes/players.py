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
        # try to convert the wagon_id to an integer if it is not already an integer 
        try:
            wagon_index = int(wagon_id.split("-")[1])
        except ValueError:
            logger.error(f"Invalid wagon_id: {wagon_id}")
            raise HTTPException(status_code=404, detail="Invalid wagon_id")
        
        try:
            # First check if player_details is contained in the loaded data
            if  len(player_details) == 0:
                logger.error("Missing 'player_details' key in loaded data")
                raise HTTPException(status_code=404, detail="Player details not found")
            
            # players is a list of dictionaries, so we need to filter the list for the player_id    
            player_info = next((player for player in player_details[wagon_index]["players"] if player["playerId"] == player_id), None)
            # check if player_info is found
            if player_info is None:
                logger.error(f"Player info not found | wagon: {wagon_id} | player: {player_id}")
                raise HTTPException(status_code=404, detail="Player info not found")
            
            logger.debug(
                f"Found player info | wagon: {wagon_id} | player: {player_id} | profile_exists: {'profile' in player_info}"
            )

            # first check if names is contained in the loaded data
            if len(names) == 0:
                logger.error("Missing 'names' key in loaded data")
                raise HTTPException(status_code=404, detail="Names not found")
            
            # "players" is a list of dictionaries, so we need to filter the list for the player_id  
            name_info = next((player for player in names[wagon_index]["players"] if player["playerId"] == player_id), None)
            # check if name_info is found
            if name_info is None:
                logger.error(f"Name info not found | wagon: {wagon_id} | player: {player_id}")
                raise HTTPException(status_code=404, detail="Name info not found")
            
            logger.debug(
                f"Found name info | wagon: {wagon_id} | player: {player_id}"
            )
            
            # Combine information
            player_in_current_wagon_info = {
                "id": player_id,
                "name_info": name_info,
                "profile": player_info.get("profile", {})
            }
            
            # Filter properties if specified
            if properties:
                logger.info(
                    f"Filtering player info | requested_properties: {properties} | available_properties: {list(player_in_current_wagon_info.keys())}"
                )
            
            logger.info("Successfully retrieved complete player info")
            return player_in_current_wagon_info
            
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

    # try catch for wagon_index
    try:
        wagon_index = int(wagon_id.split("-")[1])
    except ValueError:
        logger.error(f"Invalid wagon_id: {wagon_id}")
        raise HTTPException(status_code=404, detail="Invalid wagon_id")

    wagon_index = int(wagon_id.split("-")[1])
    
    try:
        # Load data based on default_game flag
        names, player_details, _ = FileManager.load_session_data(session_id, session.default_game)
        
        if len(player_details) == 0:
            # check if player_details is contained in the loaded data
            logger.error("player_details is empty")
            raise HTTPException(status_code=404, detail="Player details not found")
        
        # Check if player details exists for the wagon_index
        # should check whether None or empty list
        if not player_details[wagon_index]["players"]:
            logger.error(f"Player details not found for wagon_index={wagon_index}")
            raise HTTPException(status_code=404, detail="Player details not found")
            
        players_in_current_wagon = player_details[wagon_index]["players"]
        logger.debug(f"Found player info | wagon={wagon_id} | player_count={len(players_in_current_wagon)}")

        # check if names is contained in the loaded data
        if len(names) == 0:
            logger.error("names is empty")
            raise HTTPException(status_code=404, detail="Names not found")
        
        names_in_current_wagon = names[wagon_index]
        logger.debug(f"Found name info | wagon={wagon_id} | name_count={len(names_in_current_wagon)}")
        
        # Create dictionaries for quick lookup by player ID
        name_info = {
            player["playerId"]: player 
            for player in names_in_current_wagon["players"]
        }
        
        player_info = {
            player["playerId"]: player
            for player in players_in_current_wagon
        }

        # Combine information for all players in the wagon
        players_in_current_wagon_info = []
        for player_id in player_info:
            logger.debug(f"Processing player | wagon={wagon_id} | player={player_id}")
            complete_info = {
                "id": player_id,
                "name_info": name_info.get(player_id, {}),
                "profile": player_info[player_id].get("profile", {})
            }
            players_in_current_wagon_info.append(complete_info)

        logger.info(f"Successfully retrieved all players | wagon={wagon_id} | player_count={len(players_in_current_wagon_info)}")
        return {"players": players_in_current_wagon_info}
            
    except FileNotFoundError as e:
        logger.error(f"Failed to load session data | error={str(e)} | session_id={session_id}")
        raise HTTPException(status_code=404, detail="Session data not found")
    except Exception as e:
        logger.error(f"Unexpected error | error={str(e)} | wagon_id={wagon_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

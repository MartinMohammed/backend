from fastapi import APIRouter, HTTPException
from app.services.generate_train.generate_train import GenerateTrainService
from app.models.train import GenerateTrainResponse
from app.utils.file_management import FileManager
from app.core.logging import get_logger
from app.services.session_service import SessionService
import json 


router = APIRouter(
    prefix="/api/generate",
    tags=["train-generation"]
)

logger = get_logger("generate")

@router.get("/train/{session_id}/{number_of_wagons}/{theme}")
async def get_generated_train(
    session_id: str,
    number_of_wagons: str,
    theme: str
):
    """
    Generate a new train with specified parameters for a session.
    
    - Validates the session exists
    - Creates wagons with theme-appropriate passcodes
    - Generates passengers with names and profiles
    - Stores the generated data for the session
    - Returns the complete train data structure
    """
    session = SessionService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        number_of_wagons = int(number_of_wagons)
    except ValueError:
        raise HTTPException(status_code=400, detail="number_of_wagons must be an integer")

    if number_of_wagons <= 0:
        raise HTTPException(status_code=400, detail="number_of_wagons must be greater than 0")
        
    if number_of_wagons > 6:
        raise HTTPException(status_code=400, detail="number_of_wagons cannot exceed 6")

    try:
        generate_train_service = GenerateTrainService()
        names_data, player_details_data, wagons_data = generate_train_service.generate_train(theme, number_of_wagons)
        
        # Save the raw data
        FileManager.save_session_data(session_id, names_data, player_details_data, wagons_data)

        # Construct response with proper schema
        response = {
            "names": names_data,
            "player_details": player_details_data,
            "wagons": wagons_data
        }

        logger.info(f"Setting default_game to False | session_id={session_id}")
        session.default_game = False 
        SessionService.update_session(session)
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate train for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate train: {str(e)}")
      
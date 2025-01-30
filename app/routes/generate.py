from fastapi import APIRouter, HTTPException, Depends
from app.services.generate_train.generate_train import GenerateTrainService
from app.services.generate_train.generate_train import GenerateTrainService
from app.models.train import GenerateTrainResponse, Names, PlayerDetailsResponse, WagonsResponse
from app.utils.file_management import FileManager
from app.core.logging import get_logger
from app.services.session_service import SessionService


router = APIRouter(
    prefix="/api/generate",
    tags=["train-generation"]
)

logger = get_logger("generate")

@router.get(
    "/train/{session_id}/{number_of_wagons}/{theme}",
    response_model=GenerateTrainResponse,
    summary="Generate a new train for a session",
    description="""
    Generates a new train with the specified number of wagons and theme for a given session.
    Each wagon contains:
    - A unique passcode related to the theme
    - Multiple passengers with generated names and profiles
    - Theme-specific details and characteristics
    """,
    responses={
        200: {
            "description": "Successfully generated train data",
            "content": {
                "application/json": {
                    "example": {
                        "names": {
                            "names": {
                                "wagon-1": {
                                    "player-1": {"first_name": "John", "last_name": "Doe"}
                                }
                            }
                        },
                        "player_details": {
                            "player_details": {
                                "wagon-1": {
                                    "player-1": {"profile": {"age": 30, "occupation": "Engineer"}}
                                }
                            }
                        },
                        "wagons": {
                            "wagons": {
                                "wagon-1": {"theme": "Space", "passcode": "Nebula"}
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "example": {"detail": "number_of_wagons must be between 1 and 6"}
                }
            }
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Session not found"}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to generate train: Internal error"}
                }
            }
        }
    }
)
async def get_generated_train(
    session_id: str,
    number_of_wagons: str,
    theme: str
) -> GenerateTrainResponse:
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
        names, player_details, wagons = generate_train_service.generate_train(theme, number_of_wagons)
        FileManager.save_session_data(session_id, names, player_details, wagons)

        response = GenerateTrainResponse(
            names=Names(names=names["names"]),
            player_details=PlayerDetailsResponse(player_details=player_details["player_details"]),
            wagons=WagonsResponse(wagons=wagons["wagons"])
        )

        logger.info(f"Setting default_game to False | session_id={session_id}")
        session.default_game = False 
        # update the central state of the session 
        SessionService.update_session(session)

        return response
        
    except Exception as e:
        logger.error(f"Failed to generate train for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate train: {str(e)}")
      
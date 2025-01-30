from fastapi import APIRouter, HTTPException, Depends
from app.services.session_service import SessionService
from app.models.session import UserSession
from app.services.generate_train.generate_train import generate_train
from app.models.train import GenerateTrainResponse, Names, PlayerDetailsResponse, WagonsResponse

router = APIRouter(
    prefix="/api/generate",
    tags=["chat"]
)

@router.get("/train/{session_id}/{number_of_wagons}/{theme}", response_model=GenerateTrainResponse)
async def get_generated_train(session_id: str, number_of_wagons: str, theme: str):
    # session = SessionService.get_session(session_id)
    # if not session:
    #     raise HTTPException(status_code=404, detail="Session not found")

    # Convert and validate number_of_wagons
    try:
        number_of_wagons = int(number_of_wagons)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="number_of_wagons must be an integer"
        )

    if number_of_wagons <= 0:
        raise HTTPException(
            status_code=400,
            detail="number_of_wagons must be greater than 0"
        )
        
    if number_of_wagons > 6:
        raise HTTPException(
            status_code=400,
            detail="number_of_wagons cannot exceed 6"
        )

    # Generate train data using the existing function
    names, player_details, wagons = generate_train(theme, number_of_wagons)

    # Create Pydantic models from the response
    response = GenerateTrainResponse(
        names=Names(names=names["names"]),
        player_details=PlayerDetailsResponse(player_details=player_details["player_details"]),
        wagons=WagonsResponse(wagons=wagons["wagons"])
    )

    return response
      
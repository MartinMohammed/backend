from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from app.services.session_service import SessionService
from app.utils.file_management import FileManager

router = APIRouter(
    prefix="/api/wagons",
    tags=["wagons"]
)

@router.get("/{session_id}")
async def get_wagons(session_id: str):
    session = SessionService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Use default_game flag from session to determine data source
        wagons_data = FileManager.load_session_data(session_id, session.default_game)[2]
        return wagons_data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading wagons data: {str(e)}") 
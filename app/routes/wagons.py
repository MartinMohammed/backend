from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(
    prefix="/api/wagons",
    tags=["wagons"]
)

@router.get("/{wagon_id}")
async def get_wagon(wagon_id: int):
    try:
        file_path = Path(f"data/wagons/wagon-{wagon_id}.json")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Wagon {wagon_id} not found")
            
        with open(file_path, "r") as f:
            wagon_data = json.load(f)
        return wagon_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading wagon data") 
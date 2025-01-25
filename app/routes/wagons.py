from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(
    prefix="/api/wagons",
    tags=["wagons"]
)


@router.get("")
async def get_wagons():
    """Get all wagons data"""
    try:
        file_path = Path("data/wagons.json")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Wagons data not found")
            
        with open(file_path, "r") as f:
            wagons_data = json.load(f)
        return wagons_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading wagons data") 
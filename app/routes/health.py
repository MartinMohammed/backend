from fastapi import APIRouter, status

router = APIRouter(
    prefix="",
    tags=["health"]
)

@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "healthy",
        "message": "Service is running"
    } 
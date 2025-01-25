from fastapi import APIRouter, status, Response

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("")
async def health_check():
    """Health check endpoint for AWS ELB"""
    return Response(status_code=status.HTTP_200_OK) 
from fastapi import APIRouter, status, Response

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("")
@router.options("")  # Handle OPTIONS preflight request
async def health_check():
    """Health check endpoint for AWS ELB"""
    response = Response(status_code=status.HTTP_200_OK)
    # Add CORS headers explicitly for health checks
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response 
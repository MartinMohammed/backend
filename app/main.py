from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, wagons, chat, players
from app.core.logging import setup_logging, get_logger
from app.core.config import settings
from datetime import datetime
import time


# Setup logging
setup_logging()
logger = get_logger("main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    Game Jam Hackathon API provides endpoints for managing wagon-based gameplay, including:
    
    * 🎮 Player Management - Create and manage player profiles
    * 🚂 Wagon System - Handle wagon-related operations
    * 💬 Chat System - In-game chat functionality
    * 🎯 Game State - Track and update game state
    
    ## API Features
    
    * Real-time chat system
    * Player profile management
    * Wagon configuration and state management
    * Health monitoring
    """,
    version="1.0.0",
    contact={
        "name": "Game Jam Team",
        "url": "https://github.com/yourusername/game-jam-hackathon",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints to monitor API status",
        },
        {
            "name": "wagons",
            "description": "Operations with wagon management and configuration",
        },
        {
            "name": "chat",
            "description": "In-game chat system operations",
        },
        {
            "name": "players",
            "description": "Player profile and inventory management",
        },
    ],
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests and responses"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENV
        }
    )
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
                "environment": settings.ENV
            }
        )
        return response
        
    except Exception as e:
        # Log error
        logger.error(
            "Request failed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "environment": settings.ENV
            }
        )
        raise

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(wagons.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(players.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed", extra={"environment": settings.ENV})
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "environment": settings.ENV,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_check": f"{settings.API_V1_STR}/health",
        "wagons_endpoint": f"{settings.API_V1_STR}/wagons",
        "chat_endpoint": f"{settings.API_V1_STR}/chat",
        "players_endpoint": f"{settings.API_V1_STR}/players"
    }


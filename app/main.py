from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, wagons, chat, players
from app.core.logging import setup_logging, get_logger
from datetime import datetime
import time

# Setup logging
logger = get_logger("main")

app = FastAPI(
    title="Game Jam API",
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
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            "timestamp": datetime.utcnow().isoformat()
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
                "process_time_ms": round(process_time * 1000, 2)
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
                "error": str(e)
            }
        )
        raise

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(wagons.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(players.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Game Jam API",
        "docs_url": "/api/docs",
        "health_check": "/api/health",
        "wagons_endpoint": "/api/wagons",
        "chat_endpoint": "/api/chat",
        "players_endpoint": "/api/players"
    }


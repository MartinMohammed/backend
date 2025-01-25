from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import health, wagons, chat, players
from app.core.logging import setup_logging, get_logger
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = get_logger("main")

app = FastAPI(
    title="Game Jam API",
    description="API for Game Jam Hackathon",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
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
app.include_router(health.router)
app.include_router(wagons.router)
app.include_router(chat.router)
app.include_router(players.router)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to Game Jam API",
        "docs_url": "/docs",
        "health_check": "/health",
        "wagons_endpoint": "/api/wagons",
        "chat_endpoint": "/api/chat",
        "players_endpoint": "/api/players"
    }


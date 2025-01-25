from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, RedirectResponse
from app.routes import health, wagons, chat, players
from app.core.logging import get_logger
from dotenv import load_dotenv
from datetime import datetime
import time

# Load environment variables
load_dotenv()

# Setup logging
logger = get_logger("main")

app = FastAPI(
    title="Game Jam API",
    description="API for Game Jam Hackathon",
    version="1.0.0"
)

# Configure CORS - Allow all origins and methods with specific Unity requirements
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "*"  # Allow all headers for maximum compatibility
    ],
    expose_headers=[
        "Location",  # Important for redirects
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Credentials",
        "Access-Control-Expose-Headers",
    ],
    max_age=3600,  # Cache preflight requests for 1 hour
)

@app.middleware("http")
async def handle_redirects(request: Request, call_next):
    """Handle redirects and ensure CORS headers are present"""
    response = await call_next(request)
    
    # Always add CORS headers, especially important for redirects
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    
    # Special handling for redirects
    if response.status_code in [301, 302, 307, 308]:
        response.headers["Access-Control-Expose-Headers"] = "Location"
        # Ensure redirect goes to HTTPS
        if "Location" in response.headers:
            location = response.headers["Location"]
            if location.startswith("http://"):
                response.headers["Location"] = location.replace("http://", "https://", 1)
    
    return response

@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers - Modified to be more permissive for Unity
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Changed from DENY to SAMEORIGIN
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; connect-src *"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    
    return response

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
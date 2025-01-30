from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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

# -----------------------------------------------------------------------------
# 1. Configure CORS for Unity Web Requests
# -----------------------------------------------------------------------------
#
# Unity’s documentation highlights the need for the following CORS headers:
#   "Access-Control-Allow-Origin": "*",
#   "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
#   "Access-Control-Allow-Headers": "Accept, X-Access-Token, X-Application-Name, X-Request-Sent-Time",
#   "Access-Control-Allow-Credentials": "true" (optional, but requires NOT using "*")
#
# In this example, we allow all origins ("*") and do NOT allow credentials. 
# This is the simplest approach. If you need cookies or authentication headers,
# switch `allow_origins` to an explicit domain and set `allow_credentials=True`.
#
# Note: We also allow PUT, DELETE, etc., but that’s up to your application needs.
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "https://your-custom-domain.com" if credentials are needed
    allow_credentials=False,  # Must be False if allow_origins=["*"] in modern browsers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],  # You could limit this to ["Accept", "X-Access-Token", ...] if desired
    expose_headers=[
        "Location",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Credentials",
        "Access-Control-Expose-Headers",
    ],
    max_age=3600,  # Cache preflight requests for 1 hour
)


# -----------------------------------------------------------------------------
# 2. Middleware to handle redirects and force HTTPS in redirect Location headers
# -----------------------------------------------------------------------------
@app.middleware("http")
async def handle_redirects(request: Request, call_next):
    """Ensure CORS headers are in redirect responses and force https in the 'Location' header."""
    response = await call_next(request)
    
    # Always add the essential CORS headers (in case the built-in CORS middleware missed a redirect).
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    
    # Expose 'Location' in case the browser needs to read that header after a redirect
    if response.status_code in [301, 302, 307, 308]:
        response.headers["Access-Control-Expose-Headers"] = "Location"
        if "Location" in response.headers:
            location = response.headers["Location"]
            # Force HTTPS if the redirect is incorrectly set to http
            if location.startswith("http://"):
                response.headers["Location"] = location.replace("http://", "https://", 1)
    
    return response

# -----------------------------------------------------------------------------
# 3. Security headers (Content-Security-Policy, etc.)
# -----------------------------------------------------------------------------
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security-related headers to all responses."""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"  # More permissive than DENY
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # This tells browsers to only connect via HTTPS (for 1 year)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Example CSP that is permissive to allow 'unsafe-inline' and 'unsafe-eval'
    # for typical Unity web builds. Adjust as needed for your security posture.
    response.headers["Content-Security-Policy"] = (
        "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
        "connect-src *"
    )
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    
    return response

# -----------------------------------------------------------------------------
# 4. Logging middleware
# -----------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests and responses."""
    start_time = time.time()
    
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
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
        logger.error(
            "Request failed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "error": str(e)
            }
        )
        raise

# -----------------------------------------------------------------------------
# 5. Include your routers
# -----------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(wagons.router)
app.include_router(chat.router)
app.include_router(players.router)

# -----------------------------------------------------------------------------
# 6. Basic root endpoint
# -----------------------------------------------------------------------------
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


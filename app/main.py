from fastapi import FastAPI
from app.routes import health, wagons

app = FastAPI(
    title="Game Jam API",
    description="API for Game Jam Hackathon",
    version="1.0.0"
)

# Include routers
app.include_router(health.router)
app.include_router(wagons.router)



@app.get("/")
async def root():
    return {
        "message": "Welcome to Game Jam API",
        "docs_url": "/docs",
        "health_check": "/health",
        "wagons_endpoint": "/api/wagons/{wagon_id}"
    }


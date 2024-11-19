from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uvicorn

# Import local modules
from app.api.endpoints import router
from app.scraper.worker import ScholarshipScraper
from app.core.database import get_db

# Configuration
CORS_ORIGINS = ["*"]  
HOST = "0.0.0.0"
PORT = 8080

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    try:
        # Startup: Initialize database and start worker
        db = next(get_db())
        scraper = ScholarshipScraper(db)
        worker_task = asyncio.create_task(scraper.run_worker())
        
        yield  # Keeps the app running until shutdown
        
    finally:
        # Shutdown: Clean up worker task
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    # Create FastAPI instance with lifespan
    app = FastAPI(lifespan=lifespan)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # For production, specify your frontend domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=600,
    )
    
    # Register routes
    app.include_router(router, prefix="/api")
    
    return app

# Entry point
if __name__ == "__main__":
    app = create_application()
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
    )

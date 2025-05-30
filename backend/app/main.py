import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import search

# Load environment variables from environment.env file
load_dotenv('environment.env')

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vetting Intelligence Search Hub",
    description="A production-ready web application to search and harmonise results from multiple government data sources for compliance, due diligence, and investigative research.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Vetting Intelligence Search Hub is running",
        "version": "1.0.0"
    }

@app.get("/health")
def detailed_health_check():
    """Detailed health check with component status."""
    from app.cache import cache_service
    
    cache_stats = cache_service.get_cache_stats()
    
    return {
        "status": "ok",
        "components": {
            "api": "healthy",
            "cache": cache_stats.get('status', 'unknown')
        },
        "cache_stats": cache_stats
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error responses."""
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    ) 
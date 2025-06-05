import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import search, correlation

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
    description="A production-ready web application to search and harmonise results from multiple government data sources for compliance, due diligence, and investigative research. Now featuring advanced multi-jurisdictional correlation analysis between NYC contracts, NYC lobbying, and Federal lobbying activities.",
    version="2.0.0",
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
app.include_router(correlation.router)

# Include enhanced correlation router
try:
    from app.routers import enhanced_correlation
    app.include_router(enhanced_correlation.router)
    logger.info("✅ Enhanced correlation analysis loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Enhanced correlation analysis not available: {e}")

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Vetting Intelligence Search Hub is running with enhanced correlation analysis",
        "version": "2.0.0",
        "features": [
            "Multi-source government data search",
            "Multi-jurisdictional correlation analysis", 
            "Historical federal lobbying data",
            "Timeline analysis and strategic insights",
            "Company comparison and pattern analysis",
            "Excel/CSV export capabilities"
        ]
    }

@app.get("/health")
def detailed_health_check():
    """Detailed health check with component status."""
    from app.cache import cache_service
    
    cache_stats = cache_service.get_cache_stats()
    
    # Check for enhanced components
    enhanced_available = True
    try:
        import importlib.util
        enhanced_analyzer_spec = importlib.util.find_spec("app.enhanced_correlation_analyzer")
        enhanced_senate_spec = importlib.util.find_spec("app.adapters.enhanced_senate_lda")
        if enhanced_analyzer_spec is None or enhanced_senate_spec is None:
            enhanced_available = False
    except ImportError:
        enhanced_available = False
    
    return {
        "status": "ok",
        "components": {
            "api": "healthy",
            "cache": cache_stats.get('status', 'unknown'),
            "correlation_analyzer": "ready",
            "enhanced_correlation_analyzer": "ready" if enhanced_available else "not_available",
            "data_sources": {
                "nyc_checkbook": "available",
                "nyc_lobbyist": "available", 
                "senate_lda": "available",
                "enhanced_senate_lda": "available" if enhanced_available else "not_available",
                "house_lda": "available",
                "dbnyc": "available",
                "nys_ethics": "available"
            }
        },
        "cache_stats": cache_stats,
        "version": "2.0.0",
        "enhanced_features": {
            "google_scale_analysis": enhanced_available,
            "advanced_correlation_metrics": enhanced_available,
            "multi_company_comparison": enhanced_available,
            "quarterly_trend_analysis": enhanced_available,
            "strategic_insights": enhanced_available
        }
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
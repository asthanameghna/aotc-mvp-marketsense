"""
MarketSense FastAPI Backend
Production-ready API for anomaly detection, sentiment analysis, and risk assessment
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router
from api.dependencies import get_cache_service, get_market_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting MarketSense API...")
    
    # Initialize services
    cache = get_cache_service()
    market = get_market_service()
    
    # Test connectivity
    if market.test_connectivity():
        logger.info("✅ Yahoo Finance connectivity verified")
    else:
        logger.warning("⚠️ Yahoo Finance connectivity test failed")
    
    logger.info("✅ MarketSense API is ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MarketSense API...")
    cache.clear()
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="MarketSense API",
    description="""
    **MarketSense** is a professional-grade financial intelligence API that detects market anomalies in real-time.
    
    ## Features
    
    * **Multi-Modal Fusion**: Combines Market Data (Price/Volume) and NLP (News Sentiment)
    * **Unsupervised Learning**: Uses Isolation Forest ML model for anomaly detection
    * **Advanced Technicals**: RSI, Bollinger Bands, MACD, VWAP, and more
    * **Sentiment Engine**: Real-time news sentiment analysis with VADER
    * **Fast Responses**: Intelligent caching with 5-minute TTL
    
    ## Endpoints
    
    * `/api/v1/stocks/{ticker}/analysis` - Get complete analysis for a single stock
    * `/api/v1/stocks/batch` - Analyze multiple stocks at once
    * `/api/v1/watchlist` - Manage your stock watchlist
    * `/api/v1/health` - API health check and statistics
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint with basic information.
    """
    return {
        "name": "MarketSense API",
        "version": "1.0.0",
        "description": "AI-Powered Market Anomaly Detection",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 80)
    logger.info("🏭 MARKETSENSE - FASTAPI BACKEND")
    logger.info("=" * 80)
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

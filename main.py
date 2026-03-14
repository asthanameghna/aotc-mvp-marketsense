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
from database.connection import init_database, check_connection
from background_jobs import ingest_news_job, ingest_market_data_job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import os

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
    
    # Initialize database tables (creates market_sense.db and tables on Render)
    try:
        init_database()
        if check_connection():
            logger.info("✅ Database initialized and verified")
        else:
            logger.error("❌ Database initialization failed verification")
    except Exception as e:
        logger.error(f"❌ CRITICAL: Database initialization failed: {e}")
    
    # Initialize services
    cache = get_cache_service()
    market = get_market_service()
    
    # Test connectivity
    if market.test_connectivity():
        logger.info("✅ Yahoo Finance connectivity verified")
    else:
        logger.warning("⚠️ Yahoo Finance connectivity test failed")
    
    # Start background scheduler
    NEWS_INTERVAL = int(os.getenv('NEWS_INTERVAL_MINUTES', '5'))
    MARKET_DATA_INTERVAL = int(os.getenv('MARKET_DATA_INTERVAL_MINUTES', '15'))
    
    # Check if we have any data. If not, trigger an immediate ingestion
    from database import crud
    from database.connection import SessionLocal
    db = SessionLocal()
    has_data = False
    try:
        watchlist = load_watchlist()
        if watchlist:
            first_ticker = watchlist[0]
            analysis = crud.get_complete_analysis(db, first_ticker)
            if analysis:
                has_data = True
                logger.info(f"📊 Existing data found for {first_ticker}, skipping initial sync.")
            else:
                logger.info("🔍 No data found in database. Initial sync required.")
    except Exception as e:
        logger.error(f"Error checking for existing data: {e}")
    finally:
        db.close()

    scheduler = BackgroundScheduler()
    
    # Give the database 2 seconds to be ready
    start_time = datetime.now() + timedelta(seconds=2)
    
    # If no data, run once immediately
    if not has_data:
        logger.info("🚀 Triggering immediate data ingestion for faster first-load...")
        scheduler.add_job(
            ingest_news_job,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=1),
            id='initial_news_sync'
        )
        scheduler.add_job(
            ingest_market_data_job,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=5),
            id='initial_market_sync'
        )

    scheduler.add_job(
        ingest_news_job,
        trigger=IntervalTrigger(minutes=NEWS_INTERVAL),
        id='news_ingestion',
        name='News Ingestion Job',
        next_run_time=start_time + timedelta(minutes=NEWS_INTERVAL) if not has_data else start_time,
        replace_existing=True
    )
    scheduler.add_job(
        ingest_market_data_job,
        trigger=IntervalTrigger(minutes=MARKET_DATA_INTERVAL),
        id='market_data_ingestion',
        name='Market Data Ingestion Job',
        next_run_time=start_time + timedelta(minutes=MARKET_DATA_INTERVAL) if not has_data else start_time,
        replace_existing=True
    )
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info(f"✅ Background scheduler started (News: {NEWS_INTERVAL}m, Market: {MARKET_DATA_INTERVAL}m)")
    
    logger.info("✅ MarketSense API is ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down MarketSense API...")
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown()
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


from fastapi.staticfiles import StaticFiles

# Mount frontend as static files on the root
# This allows the API and the web app to run on the exact same port!
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


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

"""
MarketSense API Routes (Database-Backed)
FastAPI endpoints that serve pre-computed data from database
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from api.models import (
    StockAnalysisResponse,
    WatchlistRequest,
    WatchlistResponse,
    HealthResponse,
    ErrorResponse,
    CacheStats
)
from api.dependencies import get_cache_service
from services.cache_service import CacheService
from database import get_db, crud
from config import load_watchlist, save_watchlist

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["MarketSense API"])


# ============================================================================
# Stock Analysis Endpoints (Database-Backed)
# ============================================================================

@router.get(
    "/stocks/{ticker}/analysis",
    response_model=StockAnalysisResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Stock not found"},
        500: {"model": ErrorResponse, "description": "Analysis failed"}
    },
    summary="Get stock analysis from database",
    description="Retrieve complete pre-computed analysis for a single stock"
)
async def get_stock_analysis(
    ticker: str,
    db: Session = Depends(get_db)
) -> StockAnalysisResponse:
    """Get complete analysis from database (fast, no computation)."""
    ticker = ticker.upper()
    
    # Get complete analysis from database
    analysis = crud.get_complete_analysis(db, ticker)
    
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data available for {ticker}. Background jobs may not have run yet."
        )
    
    return StockAnalysisResponse(**analysis)


@router.get(
    "/stocks/batch",
    response_model=List[StockAnalysisResponse],
    summary="Get batch stock analysis from database"
)
async def get_batch_analysis(
    tickers: List[str] = None,
    db: Session = Depends(get_db)
) -> List[StockAnalysisResponse]:
    """Analyze multiple stocks from database."""
    if not tickers:
        tickers = load_watchlist()
    else:
        tickers = [t.upper() for t in tickers]
    
    results = []
    for ticker in tickers:
        analysis = crud.get_complete_analysis(db, ticker)
        if analysis:
            results.append(StockAnalysisResponse(**analysis))
    
    return results


# ============================================================================
# Individual Component Endpoints
# ============================================================================

@router.get("/anomaly/{ticker}", summary="Get anomaly score")
async def get_anomaly(ticker: str, db: Session = Depends(get_db)):
    """Get latest anomaly score for a ticker."""
    ticker = ticker.upper()
    anomaly = crud.get_latest_anomaly(db, ticker)
    
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"No anomaly data for {ticker}")
    
    return anomaly


@router.get("/sentiment/{ticker}", summary="Get sentiment analysis")
async def get_sentiment(ticker: str, db: Session = Depends(get_db)):
    """Get latest sentiment analysis for a ticker."""
    ticker = ticker.upper()
    sentiment = crud.get_latest_sentiment(db, ticker)
    
    if sentiment['headline_count'] == 0:
        raise HTTPException(status_code=404, detail=f"No sentiment data for {ticker}")
    
    return sentiment


@router.get("/risk/{ticker}", summary="Get risk assessment")
async def get_risk(ticker: str, db: Session = Depends(get_db)):
    """Get latest risk assessment for a ticker."""
    ticker = ticker.upper()
    risk = crud.get_latest_risk(db, ticker)
    
    if not risk:
        raise HTTPException(status_code=404, detail=f"No risk data for {ticker}")
    
    return risk


# ============================================================================
# Watchlist Management
# ============================================================================

@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist() -> WatchlistResponse:
    """Get current watchlist."""
    tickers = load_watchlist()
    return WatchlistResponse(tickers=tickers, count=len(tickers))


@router.post("/watchlist", response_model=WatchlistResponse)
async def update_watchlist(request: WatchlistRequest) -> WatchlistResponse:
    """Update watchlist."""
    tickers = [t.upper().strip() for t in request.tickers if t.strip()]
    
    if not tickers:
        raise HTTPException(status_code=400, detail="Watchlist cannot be empty")
    
    try:
        save_watchlist(tickers)
        logger.info(f"Watchlist updated: {tickers}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save watchlist: {str(e)}")
    
    return WatchlistResponse(tickers=tickers, count=len(tickers))


# ============================================================================
# System Endpoints
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check(
    cache: CacheService = Depends(get_cache_service),
    db: Session = Depends(get_db)
) -> HealthResponse:
    """API health check."""
    stats = cache.get_stats()
    
    # Check database connection
    try:
        from database.connection import check_connection
        db_connected = check_connection()
    except Exception:
        db_connected = False
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now().isoformat(),
        cache_stats=CacheStats(**stats),
        data_source_connected=db_connected
    )

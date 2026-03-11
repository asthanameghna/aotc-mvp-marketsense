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
    CacheStats,
    HistoricalDataResponse,
    HistoricalDataPoint
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
# Historical Data Endpoints
# ============================================================================

@router.get(
    "/stocks/{ticker}/history",
    response_model=HistoricalDataResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Stock history not found"}
    },
    summary="Get historical price data",
    description="Retrieve historical market data points for chart rendering"
)
async def get_historical_data(
    ticker: str,
    days: int = 365,
    db: Session = Depends(get_db)
) -> HistoricalDataResponse:
    """Get historical market data directly from Yahoo Finance."""
    import yfinance as yf
    import pandas as pd
    
    ticker = ticker.upper()
    
    try:
        # We need calendar days, but yf period expects d, mo, y
        # However, for specific days > 730d it might be better to use 'y' if large, 
        # but 'd' generally works or we can just calculate a start date.
        # Another approach: use exact start and end dates.
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        data = yf.download(ticker, start=start_date, progress=False)
        
        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data available for {ticker}."
            )
            
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        data_points = []
        for index, row in data.iterrows():
            # Skip rows with NaNs in Close
            if pd.isna(row.get('Close')): continue
                
            data_points.append(
                HistoricalDataPoint(
                    timestamp=index.isoformat(),
                    open=float(row.get('Open', 0)),
                    high=float(row.get('High', 0)),
                    low=float(row.get('Low', 0)),
                    close=float(row.get('Close', 0)),
                    volume=int(row.get('Volume', 0))
                )
            )
            
        return HistoricalDataResponse(
            ticker=ticker,
            count=len(data_points),
            data=data_points
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch historical data: {str(e)}"
        )


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
# On-Demand Data Ingestion
# ============================================================================

@router.post("/stocks/{ticker}/ingest", summary="Ingest stock data on-demand")
async def ingest_stock_on_demand(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    Immediately fetch and process data for a single stock.
    This allows instant analysis for newly added stocks without waiting for background jobs.
    """
    ticker = ticker.upper()
    logger.info(f"📊 On-demand ingestion requested for {ticker}")
    
    try:
        from yahoo_finance_fetcher import YahooFinanceDataFetcher, clean_market_data
        from feature_engineering import FeatureEngineer
        from anomaly_detection import MarketAnomalyDetector
        from news_ingestion import NewsIngestor
        from risk_assessment import calculate_risk_level
        from explainability import generate_explanation
        
        # 1. Fetch and store news
        news_ingestor = NewsIngestor()
        headlines = news_ingestor.fetch_news_for_stock(ticker)
        
        if headlines:
            analyzed_headlines, avg_sentiment = news_ingestor.sentiment_analyzer.analyze_headlines(headlines)
            crud.insert_news_headlines(db, ticker, analyzed_headlines)
            logger.info(f"✅ {ticker}: Stored {len(analyzed_headlines)} headlines")
        else:
            avg_sentiment = 0.0
            logger.warning(f"⚠️ {ticker}: No news found")
        
        # 2. Fetch market data
        fetcher = YahooFinanceDataFetcher()
        portfolio_data = fetcher.fetch_multiple_stocks([ticker], days_back=3650)
        
        if not portfolio_data or ticker not in portfolio_data:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to fetch market data for {ticker}. Please check if the ticker symbol is valid."
            )
        
        raw_data = portfolio_data[ticker]
        
        if raw_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to fetch market data for {ticker}. Please check if the ticker symbol is valid."
            )
        
        # 3. Clean data
        cleaned_data = clean_market_data(raw_data)
        if cleaned_data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No valid market data for {ticker} after cleaning"
            )
        
        # 4. Feature engineering
        feature_engineer = FeatureEngineer()
        enriched_data = feature_engineer.add_technical_indicators(cleaned_data)
        enriched_data = feature_engineer.add_sentiment_score(enriched_data, avg_sentiment)
        
        # 5. Anomaly detection
        anomaly_detector = MarketAnomalyDetector()
        analyzed_data = anomaly_detector.train_and_predict(enriched_data)
        
        # 6. Get latest data point
        latest = analyzed_data.iloc[-1]
        
        # 7. Store market data with technical indicators
        market_data_dict = {
            'timestamp': latest.name,
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'close': float(latest['Close']),
            'volume': int(latest['Volume']),
            'returns': float(latest.get('Returns', 0)),
            'log_returns': float(latest.get('Log_Returns', 0)),
            'volatility_20': float(latest.get('Volatility_20', 0)),
            'volume_change': float(latest.get('Volume_Change', 0)),
            'volume_z_score': float(latest.get('Volume_Z_Score', 0)),
            'momentum': float(latest.get('Momentum', 0)),
            'rsi_14': float(latest.get('RSI_14', 0)),
            'macd': float(latest.get('MACD', 0)),
            'macd_signal': float(latest.get('MACD_Signal', 0)),
            'macd_hist': float(latest.get('MACD_Hist', 0)),
            'bb_upper': float(latest.get('BB_Upper', 0)),
            'bb_middle': float(latest.get('BB_Middle', 0)),
            'bb_lower': float(latest.get('BB_Lower', 0)),
            'bb_pct_b': float(latest.get('BB_PctB', 0)),
            'bb_width': float(latest.get('BB_Width', 0)),
            'vwap_20': float(latest.get('VWAP_20', 0)),
            'vwap_dev': float(latest.get('VWAP_Dev', 0)),
            'z_score': float(latest.get('Z_Score', 0))
        }
        
        crud.insert_market_data(db, ticker, market_data_dict)
        
        # 8. Store anomaly score
        anomaly_score = float(latest.get('Anomaly_Score', 0))
        is_anomaly = bool(latest.get('Is_Anomaly', False))
        
        anomaly_dict = {
            'timestamp': latest.name,
            'anomaly_score': anomaly_score,
            'is_anomaly': is_anomaly,
            'features_snapshot': {
                'returns': float(latest.get('Returns', 0)),
                'volatility': float(latest.get('Volatility_20', 0)),
                'volume_z_score': float(latest.get('Volume_Z_Score', 0)),
                'sentiment': avg_sentiment
            }
        }
        
        crud.insert_anomaly(db, ticker, anomaly_dict)
        
        # 9. Calculate and store risk assessment
        risk_level = calculate_risk_level(
            anomaly_score=anomaly_score,
            volatility_z_score=float(latest.get('Volatility_20', 0)),
            sentiment_score=avg_sentiment
        )
        
        explanation = generate_explanation(latest)
        
        risk_dict = {
            'timestamp': latest.name,
            'risk_level': risk_level,
            'explanation': explanation,
            'contributing_factors': {
                'anomaly_score': anomaly_score,
                'volatility': float(latest.get('Volatility_20', 0)),
                'sentiment': avg_sentiment
            }
        }
        
        crud.insert_risk(db, ticker, risk_dict)
        
        logger.info(f"✅ {ticker}: Data ingestion complete - Anomaly={anomaly_score:.1f}, Risk={risk_level}")
        
        return {
            "success": True,
            "ticker": ticker,
            "message": f"Successfully ingested and analyzed data for {ticker}",
            "anomaly_score": anomaly_score,
            "risk_level": risk_level,
            "sentiment_score": avg_sentiment
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error ingesting {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest data for {ticker}: {str(e)}"
        )


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


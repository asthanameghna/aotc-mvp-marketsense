"""
MarketSense API Models
Pydantic models for request/response validation and serialization
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# Response Models
# ============================================================================

class PriceData(BaseModel):
    """Current price and volume data"""
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    returns: float = Field(..., description="Price returns (percentage change)")


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators"""
    rsi_14: float = Field(..., description="Relative Strength Index (14-period)")
    macd: float = Field(..., description="MACD line")
    macd_signal: float = Field(..., description="MACD signal line")
    bb_upper: float = Field(..., description="Bollinger Band upper bound")
    bb_middle: float = Field(..., description="Bollinger Band middle (SMA 20)")
    bb_lower: float = Field(..., description="Bollinger Band lower bound")
    bb_pct_b: float = Field(..., description="Bollinger Band %B indicator")
    volatility_20: float = Field(..., description="20-period volatility")
    volume_z_score: float = Field(..., description="Volume Z-Score")
    momentum: float = Field(..., description="10-period momentum")
    z_score: float = Field(..., description="Price Z-Score")


class NewsHeadline(BaseModel):
    """Individual news headline with sentiment"""
    title: str = Field(..., description="Headline title")
    source: str = Field(..., description="News source")
    link: str = Field(..., description="Article URL")
    sentiment_score: float = Field(..., description="VADER sentiment score (-1 to +1)")


class SentimentData(BaseModel):
    """News sentiment analysis results"""
    score: float = Field(..., description="Average sentiment score (-1 to +1)")
    headline_count: int = Field(..., description="Number of headlines analyzed")
    headlines: List[NewsHeadline] = Field(default_factory=list, description="Recent headlines")


class AnomalyData(BaseModel):
    """Anomaly detection results"""
    score: float = Field(..., description="Anomaly score (0-100)")
    is_anomaly: bool = Field(..., description="Whether stock is flagged as anomaly")
    threshold: float = Field(default=75.0, description="Anomaly detection threshold")


class RiskData(BaseModel):
    """Risk assessment results"""
    level: str = Field(..., description="Risk level: Low, Medium, or High")
    explanation: str = Field(..., description="Human-readable risk explanation")


class StockAnalysisResponse(BaseModel):
    """Complete stock analysis response"""
    ticker: str = Field(..., description="Stock ticker symbol")
    timestamp: str = Field(..., description="Analysis timestamp (ISO format)")
    price_data: PriceData
    technical_indicators: TechnicalIndicators
    sentiment: SentimentData
    anomaly: AnomalyData
    risk: RiskData

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "timestamp": "2026-01-30T15:00:00",
                "price_data": {
                    "open": 150.25,
                    "high": 152.10,
                    "low": 149.80,
                    "close": 151.50,
                    "volume": 75000000,
                    "returns": 0.0083
                },
                "technical_indicators": {
                    "rsi_14": 58.5,
                    "macd": 1.25,
                    "macd_signal": 1.10,
                    "bb_upper": 155.0,
                    "bb_middle": 150.0,
                    "bb_lower": 145.0,
                    "bb_pct_b": 0.65,
                    "volatility_20": 0.025,
                    "volume_z_score": 0.5,
                    "momentum": 2.5,
                    "z_score": 0.3
                },
                "sentiment": {
                    "score": 0.25,
                    "headline_count": 5,
                    "headlines": []
                },
                "anomaly": {
                    "score": 22.4,
                    "is_anomaly": False,
                    "threshold": 75.0
                },
                "risk": {
                    "level": "Low",
                    "explanation": "Normal market behavior detected"
                }
            }
        }


# ============================================================================
# Request Models
# ============================================================================

class WatchlistRequest(BaseModel):
    """Request to update watchlist"""
    tickers: List[str] = Field(..., description="List of stock ticker symbols", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["AAPL", "NVDA", "TSLA", "MSFT"]
            }
        }


class WatchlistResponse(BaseModel):
    """Current watchlist response"""
    tickers: List[str] = Field(..., description="List of stock ticker symbols")
    count: int = Field(..., description="Number of tickers in watchlist")

    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["AAPL", "NVDA", "SMR"],
                "count": 3
            }
        }


# ============================================================================
# System Models
# ============================================================================

class CacheStats(BaseModel):
    """Cache statistics"""
    entries: int = Field(..., description="Number of cached entries")
    hits: int = Field(..., description="Cache hits")
    misses: int = Field(..., description="Cache misses")
    total_requests: int = Field(..., description="Total cache requests")
    hit_rate_percent: float = Field(..., description="Cache hit rate percentage")


class HealthResponse(BaseModel):
    """API health check response"""
    status: str = Field(..., description="API status")
    timestamp: str = Field(..., description="Current timestamp")
    cache_stats: CacheStats
    data_source_connected: bool = Field(..., description="Yahoo Finance connectivity status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-01-30T15:00:00",
                "cache_stats": {
                    "entries": 5,
                    "hits": 120,
                    "misses": 30,
                    "total_requests": 150,
                    "hit_rate_percent": 80.0
                },
                "data_source_connected": True
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    ticker: Optional[str] = Field(None, description="Related ticker symbol if applicable")

"""
MarketSense Database Package
SQLAlchemy models and database management
"""

from .models import Base, Stock, MarketData, NewsHeadline, AnomalyScore, RiskAssessment
from .connection import get_db, engine, SessionLocal
from .crud import (
    get_latest_market_data,
    get_latest_anomaly,
    get_latest_sentiment,
    get_latest_risk,
    get_historical_market_data,
    insert_market_data,
    insert_news_headlines,
    insert_anomaly,
    insert_risk,
    get_complete_analysis
)

__all__ = [
    'Base', 'Stock', 'MarketData', 'NewsHeadline', 'AnomalyScore', 'RiskAssessment',
    'get_db', 'engine', 'SessionLocal',
    'get_latest_market_data', 'get_latest_anomaly', 'get_latest_sentiment',
    'get_latest_risk', 'get_historical_market_data',
    'insert_market_data', 'insert_news_headlines', 'insert_anomaly', 'insert_risk',
    'get_complete_analysis'
]

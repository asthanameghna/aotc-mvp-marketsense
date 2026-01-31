"""
MarketSense Database CRUD Operations
Create, Read, Update, Delete operations for database models
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

from .models import Stock, MarketData, NewsHeadline, AnomalyScore, RiskAssessment

logger = logging.getLogger(__name__)


# ============================================================================
# Stock Operations
# ============================================================================

def get_or_create_stock(db: Session, ticker: str, name: str = None, sector: str = None) -> Stock:
    """Get existing stock or create new one."""
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        stock = Stock(ticker=ticker, name=name, sector=sector)
        db.add(stock)
        db.commit()
        db.refresh(stock)
        logger.info(f"Created new stock: {ticker}")
    return stock


def get_all_stocks(db: Session) -> List[Stock]:
    """Get all stocks in database."""
    return db.query(Stock).all()


# ============================================================================
# Market Data Operations
# ============================================================================

def insert_market_data(db: Session, ticker: str, data: Dict) -> MarketData:
    """
    Insert market data record.
    
    Args:
        db: Database session
        ticker: Stock ticker
        data: Dictionary with market data fields
    """
    # Ensure stock exists
    get_or_create_stock(db, ticker)
    
    market_data = MarketData(ticker=ticker, **data)
    db.add(market_data)
    db.commit()
    db.refresh(market_data)
    return market_data


def get_latest_market_data(db: Session, ticker: str) -> Optional[MarketData]:
    """Get the most recent market data for a ticker."""
    return db.query(MarketData)\
        .filter(MarketData.ticker == ticker)\
        .order_by(desc(MarketData.timestamp))\
        .first()


def get_historical_market_data(db: Session, ticker: str, days: int = 30) -> List[MarketData]:
    """Get historical market data for specified number of days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    return db.query(MarketData)\
        .filter(MarketData.ticker == ticker)\
        .filter(MarketData.timestamp >= cutoff_date)\
        .order_by(MarketData.timestamp)\
        .all()


# ============================================================================
# News Operations
# ============================================================================

def insert_news_headlines(db: Session, ticker: str, headlines: List[Dict]) -> List[NewsHeadline]:
    """
    Insert multiple news headlines.
    
    Args:
        db: Database session
        ticker: Stock ticker
        headlines: List of dictionaries with headline data
    """
    # Ensure stock exists
    get_or_create_stock(db, ticker)
    
    news_records = []
    for headline in headlines:
        news = NewsHeadline(
            ticker=ticker,
            title=headline.get('title', ''),
            source=headline.get('source', ''),
            link=headline.get('link', ''),
            sentiment_score=headline.get('sentiment_score', 0.0),
            published_at=headline.get('published_at')
        )
        db.add(news)
        news_records.append(news)
    
    db.commit()
    return news_records


def get_latest_sentiment(db: Session, ticker: str, limit: int = 10) -> Dict:
    """
    Get latest sentiment analysis for a ticker.
    
    Returns:
        Dictionary with average sentiment and recent headlines
    """
    headlines = db.query(NewsHeadline)\
        .filter(NewsHeadline.ticker == ticker)\
        .order_by(desc(NewsHeadline.fetched_at))\
        .limit(limit)\
        .all()
    
    if not headlines:
        return {
            'score': 0.0,
            'headline_count': 0,
            'headlines': []
        }
    
    avg_sentiment = sum(h.sentiment_score for h in headlines) / len(headlines)
    
    return {
        'score': avg_sentiment,
        'headline_count': len(headlines),
        'headlines': [
            {
                'title': h.title,
                'source': h.source,
                'link': h.link,
                'sentiment_score': h.sentiment_score,
                'published_at': h.published_at.isoformat() if h.published_at else None
            }
            for h in headlines
        ]
    }


# ============================================================================
# Anomaly Operations
# ============================================================================

def insert_anomaly(db: Session, ticker: str, data: Dict) -> AnomalyScore:
    """
    Insert anomaly score record.
    
    Args:
        db: Database session
        ticker: Stock ticker
        data: Dictionary with anomaly data (score, is_anomaly, features_snapshot)
    """
    # Ensure stock exists
    get_or_create_stock(db, ticker)
    
    anomaly = AnomalyScore(ticker=ticker, **data)
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly


def get_latest_anomaly(db: Session, ticker: str) -> Optional[Dict]:
    """Get the most recent anomaly score for a ticker."""
    anomaly = db.query(AnomalyScore)\
        .filter(AnomalyScore.ticker == ticker)\
        .order_by(desc(AnomalyScore.timestamp))\
        .first()
    
    if not anomaly:
        return None
    
    return {
        'score': anomaly.anomaly_score,
        'is_anomaly': anomaly.is_anomaly,
        'threshold': 75.0,
        'timestamp': anomaly.timestamp.isoformat(),
        'features_snapshot': anomaly.features_snapshot
    }


def get_historical_anomalies(db: Session, ticker: str, days: int = 30) -> List[AnomalyScore]:
    """Get historical anomaly scores."""
    cutoff_date = datetime.now() - timedelta(days=days)
    return db.query(AnomalyScore)\
        .filter(AnomalyScore.ticker == ticker)\
        .filter(AnomalyScore.timestamp >= cutoff_date)\
        .order_by(AnomalyScore.timestamp)\
        .all()


# ============================================================================
# Risk Operations
# ============================================================================

def insert_risk(db: Session, ticker: str, data: Dict) -> RiskAssessment:
    """
    Insert risk assessment record.
    
    Args:
        db: Database session
        ticker: Stock ticker
        data: Dictionary with risk data (level, explanation, contributing_factors)
    """
    # Ensure stock exists
    get_or_create_stock(db, ticker)
    
    risk = RiskAssessment(ticker=ticker, **data)
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


def get_latest_risk(db: Session, ticker: str) -> Optional[Dict]:
    """Get the most recent risk assessment for a ticker."""
    risk = db.query(RiskAssessment)\
        .filter(RiskAssessment.ticker == ticker)\
        .order_by(desc(RiskAssessment.timestamp))\
        .first()
    
    if not risk:
        return None
    
    return {
        'level': risk.risk_level,
        'explanation': risk.explanation,
        'contributing_factors': risk.contributing_factors,
        'timestamp': risk.timestamp.isoformat()
    }


# ============================================================================
# Combined Operations
# ============================================================================

def get_complete_analysis(db: Session, ticker: str) -> Optional[Dict]:
    """
    Get complete analysis for a ticker (market data, sentiment, anomaly, risk).
    
    Returns:
        Dictionary with all analysis data or None if no data exists
    """
    market_data = get_latest_market_data(db, ticker)
    if not market_data:
        return None
    
    sentiment = get_latest_sentiment(db, ticker)
    anomaly = get_latest_anomaly(db, ticker)
    risk = get_latest_risk(db, ticker)
    
    return {
        'ticker': ticker,
        'timestamp': market_data.timestamp.isoformat(),
        'price_data': {
            'open': market_data.open,
            'high': market_data.high,
            'low': market_data.low,
            'close': market_data.close,
            'volume': market_data.volume,
            'returns': market_data.returns or 0.0
        },
        'technical_indicators': {
            'rsi_14': market_data.rsi_14 or 0.0,
            'macd': market_data.macd or 0.0,
            'macd_signal': market_data.macd_signal or 0.0,
            'bb_upper': market_data.bb_upper or 0.0,
            'bb_middle': market_data.bb_middle or 0.0,
            'bb_lower': market_data.bb_lower or 0.0,
            'bb_pct_b': market_data.bb_pct_b or 0.0,
            'volatility_20': market_data.volatility_20 or 0.0,
            'volume_z_score': market_data.volume_z_score or 0.0,
            'momentum': market_data.momentum or 0.0,
            'z_score': market_data.z_score or 0.0
        },
        'sentiment': sentiment,
        'anomaly': anomaly or {'score': 0.0, 'is_anomaly': False, 'threshold': 75.0},
        'risk': risk or {'level': 'Unknown', 'explanation': 'No risk data available'}
    }

"""
MarketSense Database Models
SQLAlchemy ORM models for all database tables
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base


class Stock(Base):
    """
    Stock metadata table.
    Stores basic information about tracked stocks.
    """
    __tablename__ = "stocks"

    ticker = Column(String(10), primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    sector = Column(String(100), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    market_data = relationship("MarketData", back_populates="stock", cascade="all, delete-orphan")
    news_headlines = relationship("NewsHeadline", back_populates="stock", cascade="all, delete-orphan")
    anomaly_scores = relationship("AnomalyScore", back_populates="stock", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="stock", cascade="all, delete-orphan")


class MarketData(Base):
    """
    Market data and technical indicators table.
    Stores OHLCV data and all computed technical indicators.
    """
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), ForeignKey("stocks.ticker"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # OHLCV Data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Basic Features
    returns = Column(Float, nullable=True)
    log_returns = Column(Float, nullable=True)
    volatility_20 = Column(Float, nullable=True)
    volume_change = Column(Float, nullable=True)
    volume_z_score = Column(Float, nullable=True)
    momentum = Column(Float, nullable=True)
    
    # Technical Indicators
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    bb_pct_b = Column(Float, nullable=True)
    bb_width = Column(Float, nullable=True)
    vwap_20 = Column(Float, nullable=True)
    vwap_dev = Column(Float, nullable=True)
    z_score = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="market_data")


class NewsHeadline(Base):
    """
    News headlines with sentiment analysis.
    Stores news articles and their sentiment scores.
    """
    __tablename__ = "news_headlines"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), ForeignKey("stocks.ticker"), nullable=False, index=True)
    
    # News Data
    title = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    link = Column(Text, nullable=True)
    
    # Sentiment
    sentiment_score = Column(Float, nullable=False, default=0.0)
    
    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    stock = relationship("Stock", back_populates="news_headlines")


class AnomalyScore(Base):
    """
    Anomaly detection results.
    Stores anomaly scores and detection flags.
    """
    __tablename__ = "anomaly_scores"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), ForeignKey("stocks.ticker"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Anomaly Data
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    
    # Feature snapshot (JSON of features used for detection)
    features_snapshot = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="anomaly_scores")


class RiskAssessment(Base):
    """
    Risk assessment results.
    Stores risk levels and explanations.
    """
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), ForeignKey("stocks.ticker"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Risk Data
    risk_level = Column(String(20), nullable=False)  # Low, Medium, High
    explanation = Column(Text, nullable=True)
    
    # Contributing factors (JSON)
    contributing_factors = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="risk_assessments")

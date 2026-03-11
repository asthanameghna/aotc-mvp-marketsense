"""
MarketSense Background Jobs
Automated data ingestion and processing using APScheduler
"""

import logging
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database.connection import SessionLocal
from database import crud
from config import load_watchlist
from yahoo_finance_fetcher import YahooFinanceDataFetcher, clean_market_data
from feature_engineering import FeatureEngineer
from anomaly_detection import MarketAnomalyDetector
from news_ingestion import NewsIngestor
from risk_assessment import calculate_risk_level
from explainability import generate_explanation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get configuration from environment
NEWS_INTERVAL = int(os.getenv('NEWS_INTERVAL_MINUTES', '5'))
MARKET_DATA_INTERVAL = int(os.getenv('MARKET_DATA_INTERVAL_MINUTES', '15'))


def ingest_news_job():
    """
    Background job to fetch and analyze news for all watchlist stocks.
    Runs every 5 minutes by default.
    """
    logger.info("=" * 80)
    logger.info(f"📰 NEWS INGESTION JOB STARTED - {datetime.now()}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        watchlist = load_watchlist()
        news_ingestor = NewsIngestor()
        
        for ticker in watchlist:
            try:
                logger.info(f"Fetching news for {ticker}...")
                
                # Fetch news
                headlines = news_ingestor.fetch_news_for_stock(ticker)
                
                if headlines:
                    # Analyze sentiment
                    analyzed_headlines, avg_sentiment = news_ingestor.sentiment_analyzer.analyze_headlines(headlines)
                    
                    # Store in database
                    crud.insert_news_headlines(db, ticker, analyzed_headlines)
                    
                    logger.info(f"✅ {ticker}: Stored {len(analyzed_headlines)} headlines, avg sentiment: {avg_sentiment:.3f}")
                else:
                    logger.warning(f"⚠️ {ticker}: No news found")
                    
            except Exception as e:
                logger.error(f"❌ Error processing news for {ticker}: {e}")
                continue
        
        logger.info("✅ News ingestion job completed")
        
    except Exception as e:
        logger.error(f"❌ News ingestion job failed: {e}", exc_info=True)
    finally:
        db.close()


def ingest_market_data_job():
    """
    Background job to fetch market data, calculate indicators, detect anomalies, and assess risk.
    Runs every 15 minutes by default.
    """
    logger.info("=" * 80)
    logger.info(f"📊 MARKET DATA INGESTION JOB STARTED - {datetime.now()}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        watchlist = load_watchlist()
        fetcher = YahooFinanceDataFetcher()
        feature_engineer = FeatureEngineer()
        anomaly_detector = MarketAnomalyDetector()
        
        # Fetch data for all stocks
        portfolio_data = fetcher.fetch_multiple_stocks(watchlist, days_back=3650)
        
        for ticker, raw_data in portfolio_data.items():
            try:
                logger.info(f"Processing market data for {ticker}...")
                
                # 1. Clean data
                cleaned_data = clean_market_data(raw_data)
                if cleaned_data.empty:
                    logger.warning(f"⚠️ {ticker}: No valid data after cleaning")
                    continue
                
                # 2. Get latest sentiment from database
                sentiment_data = crud.get_latest_sentiment(db, ticker)
                avg_sentiment = sentiment_data.get('score', 0.0)
                
                # 3. Feature engineering
                enriched_data = feature_engineer.add_technical_indicators(cleaned_data)
                enriched_data = feature_engineer.add_sentiment_score(enriched_data, avg_sentiment)
                
                # 4. Anomaly detection
                analyzed_data = anomaly_detector.train_and_predict(enriched_data)
                
                # 5. Get latest data point
                latest = analyzed_data.iloc[-1]
                
                # 6. Store market data with technical indicators
                market_data_dict = {
                    'timestamp': latest.name,  # Index is the timestamp
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
                
                # 7. Store anomaly score
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
                
                # 8. Calculate and store risk assessment
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
                
                logger.info(f"✅ {ticker}: Anomaly={anomaly_score:.1f}, Risk={risk_level}, Sentiment={avg_sentiment:.3f}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {ticker}: {e}", exc_info=True)
                continue
        
        logger.info("✅ Market data ingestion job completed")
        
    except Exception as e:
        logger.error(f"❌ Market data ingestion job failed: {e}", exc_info=True)
    finally:
        db.close()


def main():
    """
    Main function to set up and run the background scheduler.
    """
    logger.info("=" * 80)
    logger.info("🏭 MARKETSENSE BACKGROUND WORKER")
    logger.info("=" * 80)
    logger.info(f"News ingestion interval: {NEWS_INTERVAL} minutes")
    logger.info(f"Market data ingestion interval: {MARKET_DATA_INTERVAL} minutes")
    logger.info("=" * 80)
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Add news ingestion job
    scheduler.add_job(
        ingest_news_job,
        trigger=IntervalTrigger(minutes=NEWS_INTERVAL),
        id='news_ingestion',
        name='News Ingestion Job',
        replace_existing=True
    )
    logger.info(f"✅ Scheduled news ingestion job (every {NEWS_INTERVAL} minutes)")
    
    # Add market data ingestion job
    scheduler.add_job(
        ingest_market_data_job,
        trigger=IntervalTrigger(minutes=MARKET_DATA_INTERVAL),
        id='market_data_ingestion',
        name='Market Data Ingestion Job',
        replace_existing=True
    )
    logger.info(f"✅ Scheduled market data ingestion job (every {MARKET_DATA_INTERVAL} minutes)")
    
    # Run jobs immediately on startup
    logger.info("Running initial data ingestion...")
    try:
        ingest_news_job()
        ingest_market_data_job()
    except Exception as e:
        logger.error(f"❌ Initial ingestion failed: {e}")
    
    # Start scheduler
    logger.info("=" * 80)
    logger.info("✅ Background worker started. Press Ctrl+C to stop.")
    logger.info("=" * 80)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Shutting down background worker...")
        scheduler.shutdown()
        logger.info("✅ Background worker stopped")


if __name__ == "__main__":
    main()

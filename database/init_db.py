"""
MarketSense Database Initialization
Script to create database tables and seed initial data
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_database, check_connection, SessionLocal
from database.models import Stock
from config import load_watchlist
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_watchlist():
    """Seed database with stocks from watchlist."""
    db = SessionLocal()
    try:
        watchlist = load_watchlist()
        logger.info(f"Seeding database with {len(watchlist)} stocks from watchlist...")
        
        for ticker in watchlist:
            existing = db.query(Stock).filter(Stock.ticker == ticker).first()
            if not existing:
                stock = Stock(ticker=ticker)
                db.add(stock)
                logger.info(f"  Added stock: {ticker}")
            else:
                logger.info(f"  Stock already exists: {ticker}")
        
        db.commit()
        logger.info("✅ Watchlist seeding complete")
        
    except Exception as e:
        logger.error(f"❌ Error seeding watchlist: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main initialization function."""
    logger.info("=" * 80)
    logger.info("MARKETSENSE DATABASE INITIALIZATION")
    logger.info("=" * 80)
    
    # Check connection
    if not check_connection():
        logger.error("❌ Database connection failed. Exiting.")
        return 1
    
    # Create tables
    try:
        init_database()
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return 1
    
    # Seed watchlist
    try:
        seed_watchlist()
    except Exception as e:
        logger.error(f"❌ Failed to seed watchlist: {e}")
        return 1
    
    logger.info("=" * 80)
    logger.info("✅ DATABASE INITIALIZATION COMPLETE")
    logger.info("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())

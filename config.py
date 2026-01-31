"""
MarketSense Configuration Module
Centralized configuration for watchlist and other settings
"""

import os
import logging

logger = logging.getLogger(__name__)

# Path to watchlist file
WATCHLIST_FILE = os.path.join(os.path.dirname(__file__), 'watchlist.txt')


def load_watchlist(file_path=None):
    """
    Load stock tickers from watchlist.txt
    Returns a list of ticker symbols
    
    Args:
        file_path: Optional custom path to watchlist file
    """
    path = file_path or WATCHLIST_FILE
    
    try:
        if not os.path.exists(path):
            logger.warning(f"⚠️ Watchlist file not found: {path}")
            return ['AAPL', 'NVDA', 'TSLA']  # Default fallback
        
        with open(path, 'r') as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        
        # Remove duplicates while preserving order
        tickers = list(dict.fromkeys(tickers))
        logger.info(f"✅ Loaded {len(tickers)} tickers from watchlist")
        return tickers
        
    except Exception as e:
        logger.error(f"❌ Error loading watchlist: {e}")
        return []


def save_watchlist(tickers, file_path=None):
    """
    Save stock tickers to watchlist.txt
    
    Args:
        tickers: List of ticker symbols to save
        file_path: Optional custom path to watchlist file
    """
    path = file_path or WATCHLIST_FILE
    
    try:
        with open(path, 'w') as f:
            for ticker in tickers:
                f.write(f"{ticker.upper()}\n")
        logger.info(f"✅ Saved {len(tickers)} tickers to watchlist")
    except Exception as e:
        logger.error(f"❌ Error saving watchlist: {e}")
        raise

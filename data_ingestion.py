"""
MarketSense - Production Data Ingestion Module
Fetches real market data from Yahoo Finance for anomaly detection system
"""

import pandas as pd
import time
from datetime import datetime
from yahoo_finance_fetcher import YahooFinanceDataFetcher, clean_market_data
from feature_engineering import FeatureEngineer
import logging
import argparse
from config import load_watchlist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_market_data(fetcher, watchlist, days_back):
    """
    Single iteration of data fetching and processing
    """
    print(f"\n⏰ Starting update cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # Fetch data
    portfolio_data = fetcher.fetch_multiple_stocks(watchlist, days_back=days_back)

    if not portfolio_data:
        logger.warning("❌ No data fetched this cycle")
        return

    # Initialize Feature Engineer
    fe = FeatureEngineer()

    print("\n📈 PROCESSING & FEATURE ENGINEERING")
    print("-" * 60)

    for ticker, raw_data in portfolio_data.items():
        # Clean data
        cleaned_data = clean_market_data(raw_data)
        
        # Apply Feature Engineering
        enriched_data = fe.add_technical_indicators(cleaned_data)
        
        # Get latest data point for display
        latest = enriched_data.iloc[-1]
        
        print(f"\n📊 {ticker} Update:")
        print(f"   OHLC: Op ${latest['Open']:.2f} | Hi ${latest['High']:.2f} | Lo ${latest['Low']:.2f} | Cl ${latest['Close']:.2f}")
        print(f"   Vol (20d): {latest['Volatility_20']:.4f} | Rtn: {latest['Returns']:.2%} | Z-Score: {latest['Z_Score']:.2f}")
        print(f"   RSI: {latest['RSI_14']:.1f} | BB %B: {latest['BB_PctB']:.2f} | VWAP Dev: {latest['VWAP_Dev']:.2%}")
        print(f"   MACD: {latest['MACD']:.3f} | Signal: {latest['MACD_Signal']:.3f}")

    print("\n✅ Cycle complete. Waiting for next update...")

def main():
    """
    Main data ingestion function for MarketSense
    """
    parser = argparse.ArgumentParser(description='MarketSense Data Ingestion')
    parser.add_argument('--loop', action='store_true', help='Run in a continuous 15-min loop')
    parser.add_argument('--interval', type=int, default=900, help='Seconds between updates (default: 900)')
    parser.add_argument('--tickers', nargs='+', help='List of tickers to fetch (e.g. AAPL MSFT)')
    args = parser.parse_args()

    print("=" * 80)
    print("🏭 MARKETSENSE - PRODUCTION DATA INGESTION SYSTEM")
    print("=" * 80)

    # Initialize production fetcher
    fetcher = YahooFinanceDataFetcher()

    # Test connectivity first
    print("🔍 Testing Yahoo Finance connectivity...")
    if not fetcher.test_connectivity():
        print("❌ Yahoo Finance connectivity test FAILED")
        return

    print("✅ Yahoo Finance connectivity test PASSED")

    # Define watchlist
    if args.tickers:
        watchlist = [t.upper() for t in args.tickers]
        print(f"📋 Custom Watchlist: {', '.join(watchlist)}")
    else:
        # Load from shared file
        watchlist = load_watchlist()
        print(f"📋 Loaded Watchlist: {', '.join(watchlist)}")
    
    days_back = 365 

    if args.loop:
        print(f"🔄 Starting continuous loop (Interval: {args.interval}s)")
        try:
            while True:
                process_market_data(fetcher, watchlist, days_back)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n⚠️ Stopped by user")
    else:
        # Run once
        process_market_data(fetcher, watchlist, days_back)

    print("\n" + "=" * 80)
    print("✅ DATA INGESTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Fatal error in data ingestion: {e}")
        raise

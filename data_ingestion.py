"""
MarketSense - Production Data Ingestion Module
Fetches real market data from Yahoo Finance AND Google News for anomaly detection system
"""

import pandas as pd
import time
from datetime import datetime
from yahoo_finance_fetcher import YahooFinanceDataFetcher, clean_market_data
from feature_engineering import FeatureEngineer
from anomaly_detection import MarketAnomalyDetector
from news_ingestion import NewsIngestor
from risk_assessment import calculate_risk_level
from explainability import generate_explanation
import logging
import argparse
from config import load_watchlist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_market_data(fetcher, news_ingestor, watchlist, days_back):
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

    # Initialize Modules
    fe = FeatureEngineer()
    detector = MarketAnomalyDetector()

    print("\n📈 PROCESSING, SENTIMENT ANALYSIS & ANOMALY DETECTION")
    print("-" * 60)

    for ticker, raw_data in portfolio_data.items():
        # 1. Cleaning
        cleaned_data = clean_market_data(raw_data)
        
        # 2. Fetch News & Sentiment
        # Note: In a real high-frequency system, this would be async.
        # For this MVP, we fetch synchronously.
        headlines = news_ingestor.fetch_news_for_stock(ticker)
        
        # Analyze sentiment
        # We reuse the analyzer embedded in news_ingestor, but ideally it should be separate.
        # news_ingestor.sentiment_analyzer is available.
        if headlines:
            _, avg_sentiment = news_ingestor.sentiment_analyzer.analyze_headlines(headlines)
        else:
            avg_sentiment = 0.0 # Neutral if no news
            
        sentiment_text = f"{avg_sentiment:+.2f}"
        if avg_sentiment > 0.1: sentiment_icon = "🟢"
        elif avg_sentiment < -0.1: sentiment_icon = "🔴"
        else: sentiment_icon = "⚪"
        
        # 3. Feature Engineering
        enriched_data = fe.add_technical_indicators(cleaned_data)
        
        # 4. Inject Sentiment
        try:
            enriched_data = fe.add_sentiment_score(enriched_data, avg_sentiment)
        except Exception as e:
            logger.error(f"Failed to add sentiment: {e}")
            continue

        # 5. Anomaly Detection (Now uses Sentiment as a feature!)
        analyzed_data = detector.train_and_predict(enriched_data)
        
        # Get latest data point for display
        latest = analyzed_data.iloc[-1]
        
        # Extract Anomaly Info
        anomaly_score = latest.get('Anomaly_Score', 0)
        is_anomaly = latest.get('Is_Anomaly', False)
        
        # 6. Risk & Explainability [NEW]
        risk_level = calculate_risk_level(
            anomaly_score=anomaly_score,
            volatility_z_score=latest.get('Volatility_20', 0), # Using Volatility_20 as proxy if Z-Score not explicit
            sentiment_score=avg_sentiment
        )
        
        explanation = generate_explanation(latest)
        
        status_icon = "🔴" if is_anomaly else "🟢"
        
        print(f"\n📊 {ticker} Update:")
        print(f"   OHLC: Op ${latest['Open']:.2f} | Cl ${latest['Close']:.2f} | Vol: {latest['Volume']:.0f}")
        print(f"   Rtn: {latest['Returns']:.2%} | Z-Score: {latest['Z_Score']:.2f} | Momentum: {latest['Momentum']:.2f}")
        print(f"   📰 Sentiment: {sentiment_icon} {sentiment_text} (Based on {len(headlines)} headlines)")
        print(f"   ⚠️ Risk Level: {risk_level}")
        print(f"   ℹ️  Analysis: {explanation}")
        print(f"   {status_icon} ANOMALY SCORE: {anomaly_score:.1f}/100 | Detected: {is_anomaly}")

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
    print("🏭 MARKETSENSE - MULTI-MODAL ANOMALY DETECTION SYSTEM")
    print("=" * 80)

    # Initialize production fetchers
    fetcher = YahooFinanceDataFetcher()
    news_ingestor = NewsIngestor()

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
        watchlist = load_watchlist()
        print(f"📋 Loaded Watchlist: {', '.join(watchlist)}")
    
    days_back = 3650 

    if args.loop:
        print(f"🔄 Starting continuous loop (Interval: {args.interval}s)")
        try:
            while True:
                process_market_data(fetcher, news_ingestor, watchlist, days_back)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n⚠️ Stopped by user")
    else:
        # Run once
        process_market_data(fetcher, news_ingestor, watchlist, days_back)

    print("\n" + "=" * 80)
    print("✅ DATA INGESTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Fatal error in data ingestion: {e}")
        raise

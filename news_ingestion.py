"""
MarketSense - News Ingestion Module
Aggregates near real-time financial news from trusted sources via Google News RSS.
"""

import feedparser
import time
import urllib.parse
from datetime import datetime
import logging
import argparse

from sentiment_analysis import SentimentAnalyzer

from sentiment_analysis import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsIngestor:
    """
    Fetches and standardizes financial news from RSS feeds.
    Targeting specific stocks and high-integrity publishers.
    """

    def __init__(self):
        # List of trusted publishers
        self.trusted_publishers = [
            "reuters.com",
            "bloomberg.com",
            "cnbc.com",
            "ft.com",
            "wsj.com"
        ]
        self.base_url = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        self.sentiment_analyzer = SentimentAnalyzer()

    def construct_query(self, ticker):
        """
        Constructs a query targeting a specific stock AND trusted publishers.
        Query: (TICKER) AND (site:reuters.com OR ...)
        """
        # Create the site filter string
        site_filters = " OR ".join([f"site:{site}" for site in self.trusted_publishers])
        
        # Combine ticker and site filters
        # Using simply the ticker symbol often works, but adding "stock" or company name might be safer.
        # For MVP, Ticker is fine (e.g. NVDA, AAPL).
        full_query = f"({ticker}) AND ({site_filters}) when:1d"
        
        # URL encode
        encoded_query = urllib.parse.quote(full_query)
        return self.base_url.format(query=encoded_query)

    def fetch_news_for_stock(self, ticker):
        """
        Fetch news for a specific stock.
        """
        url = self.construct_query(ticker)
        logger.info(f"📰 Fetching news for ${ticker}...")
        
        try:
            feed = feedparser.parse(url)
            
            if not feed.entries:
                return []

            headlines = []
            for entry in feed.entries[:5]: # Top 5 headlines per stock is enough
                source = entry.get('source', {}).get('title', 'Unknown Source')
                headlines.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published,
                    'source': source
                })
            
            return headlines

        except Exception as e:
            logger.error(f"❌ Error fetching news for {ticker}: {e}")
            return []

    def get_verdict(self, score):
        """
        Return verdict based on sentiment score.
        """
        if score > 0.15:
            return "🟢 BUY", "Positive"
        elif score < -0.15:
            return "🔴 SELL", "Negative"
        else:
            return "⚪ HOLD", "Neutral"

    def run_loop(self, tickers, interval=300):
        """
        Run the ingestion loop for specific tickers.
        """
        print(f"🔄 Starting News Ingestion Loop (Interval: {interval}s)")
        print(f"📋 Watchlist: {', '.join(tickers)}")
        
        try:
            while True:
                print("\n" + "=" * 60)
                print(f"📢 MARKET SENSE UPDATE | {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 60)

                for ticker in tickers:
                    headlines = self.fetch_news_for_stock(ticker)
                    
                    if not headlines:
                        print(f"\n⚠️ No recent news for {ticker}")
                        continue

                    # Analyze
                    headlines, avg_score = self.sentiment_analyzer.analyze_headlines(headlines)
                    verdict_icon, sentiment_text = self.get_verdict(avg_score)

                    # Display Stock Card
                    print(f"\n📊 {ticker} Analysis")
                    print("-" * 40)
                    print(f"   Sentiment: {avg_score:+.2f} ({sentiment_text})")
                    print(f"   Verdict:   {verdict_icon}")
                    print("-" * 40)
                    
                    for i, item in enumerate(headlines, 1):
                        print(f"   {i}. [{item['source']}] {item['title']}")
                        # print(f"      🔗 {item['link']}") # Optional: Keep output clean

                print(f"\n⏳ Waiting {interval} seconds...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")

from config import load_watchlist

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MarketSense News Ingestion')
    parser.add_argument('--interval', type=int, default=300, help='Update interval in seconds')
    parser.add_argument('--tickers', nargs='+', help='List of tickers')
    args = parser.parse_args()

    ingestor = NewsIngestor()
    # Normalize tickers
    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        tickers = load_watchlist()
        print(f"📋 Loaded Watchlist: {', '.join(tickers)}")
        
    ingestor.run_loop(tickers, args.interval)

"""
MarketSense - Sentiment Analysis Module
Analyzes financial news headlines using VADER to gauge market sentiment.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyzes text sentiment for financial markets.
    """

    def __init__(self):
        try:
            self.analyzer = SentimentIntensityAnalyzer()
            logger.info("✅ VADER Sentiment Analyzer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize VADER: {e}")
            self.analyzer = None

    def analyze_text(self, text):
        """
        Analyze a single string and return the compound score.
        Score range: -1.0 (Most Negative) to 1.0 (Most Positive)
        """
        if not self.analyzer or not text:
            return 0.0
        
        try:
            scores = self.analyzer.polarity_scores(text)
            return scores['compound']
        except Exception:
            return 0.0

    def analyze_headlines(self, headlines):
        """
        Analyze a list of headline dictionaries.
        Adds 'sentiment_score' to each item in place.
        Returns the modified list and the average sentiment.
        """
        if not headlines:
            return headlines, 0.0

        scores = []
        for item in headlines:
            # Combine title and source for context, though source might bias. 
            # Ideally just title is cleaner for pure news sentiment.
            text = item.get('title', '')
            score = self.analyze_text(text)
            item['sentiment_score'] = score
            scores.append(score)

        avg_sentiment = statistics.mean(scores) if scores else 0.0
        return headlines, avg_sentiment

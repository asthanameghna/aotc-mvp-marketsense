"""
MarketSense Market Service
Orchestrates data fetching, analysis, and processing for API endpoints
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime

from yahoo_finance_fetcher import YahooFinanceDataFetcher, clean_market_data
from feature_engineering import FeatureEngineer
from anomaly_detection import MarketAnomalyDetector
from news_ingestion import NewsIngestor
from risk_assessment import calculate_risk_level
from explainability import generate_explanation

logger = logging.getLogger(__name__)


class MarketService:
    """
    Core service that orchestrates market data analysis.
    Integrates all MarketSense modules for comprehensive stock analysis.
    """

    def __init__(self):
        """Initialize the market service with all required components."""
        self.fetcher = YahooFinanceDataFetcher()
        self.news_ingestor = NewsIngestor()
        self.feature_engineer = FeatureEngineer()
        self.anomaly_detector = MarketAnomalyDetector()
        logger.info("✅ Market service initialized")

    def get_stock_analysis(self, ticker: str, days_back: int = 365) -> Optional[Dict]:
        """
        Perform complete analysis for a single stock.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            days_back: Number of days of historical data to fetch
            
        Returns:
            Dictionary with complete analysis or None if failed
        """
        try:
            ticker = ticker.upper()
            logger.info(f"Starting analysis for {ticker}")

            # 1. Fetch market data (using fetch_multiple_stocks for single ticker)
            portfolio_data = self.fetcher.fetch_multiple_stocks([ticker], days_back=days_back)
            
            if not portfolio_data or ticker not in portfolio_data:
                logger.warning(f"No market data available for {ticker}")
                return None
            
            raw_data = portfolio_data[ticker]
            if raw_data is None or raw_data.empty:
                logger.warning(f"Empty market data for {ticker}")
                return None

            # 2. Clean data
            cleaned_data = clean_market_data(raw_data)
            if cleaned_data.empty:
                logger.warning(f"Data cleaning failed for {ticker}")
                return None

            # 3. Fetch news and analyze sentiment
            headlines = self.news_ingestor.fetch_news_for_stock(ticker)
            if headlines:
                _, avg_sentiment = self.news_ingestor.sentiment_analyzer.analyze_headlines(headlines)
            else:
                avg_sentiment = 0.0
                headlines = []

            # 4. Feature engineering
            enriched_data = self.feature_engineer.add_technical_indicators(cleaned_data)
            enriched_data = self.feature_engineer.add_sentiment_score(enriched_data, avg_sentiment)

            # 5. Anomaly detection
            analyzed_data = self.anomaly_detector.train_and_predict(enriched_data)

            # 6. Extract latest data point
            latest = analyzed_data.iloc[-1]

            # 7. Calculate risk level
            anomaly_score = float(latest.get('Anomaly_Score', 0))
            is_anomaly = bool(latest.get('Is_Anomaly', False))
            volatility = float(latest.get('Volatility_20', 0))
            
            risk_level = calculate_risk_level(
                anomaly_score=anomaly_score,
                volatility_z_score=volatility,
                sentiment_score=avg_sentiment
            )

            # 8. Generate explanation
            explanation = generate_explanation(latest)

            # 9. Build response
            result = {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'price_data': {
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'close': float(latest['Close']),
                    'volume': int(latest['Volume']),
                    'returns': float(latest.get('Returns', 0))
                },
                'technical_indicators': {
                    'rsi_14': float(latest.get('RSI_14', 0)),
                    'macd': float(latest.get('MACD', 0)),
                    'macd_signal': float(latest.get('MACD_Signal', 0)),
                    'bb_upper': float(latest.get('BB_Upper', 0)),
                    'bb_middle': float(latest.get('BB_Middle', 0)),
                    'bb_lower': float(latest.get('BB_Lower', 0)),
                    'bb_pct_b': float(latest.get('BB_PctB', 0)),
                    'volatility_20': volatility,
                    'volume_z_score': float(latest.get('Volume_Z_Score', 0)),
                    'momentum': float(latest.get('Momentum', 0)),
                    'z_score': float(latest.get('Z_Score', 0))
                },
                'sentiment': {
                    'score': avg_sentiment,
                    'headline_count': len(headlines),
                    'headlines': [
                        {
                            'title': h.get('title', ''),
                            'source': h.get('source', ''),
                            'link': h.get('link', ''),
                            'sentiment_score': h.get('sentiment_score', 0)
                        }
                        for h in headlines[:10]  # Limit to top 10 headlines
                    ]
                },
                'anomaly': {
                    'score': anomaly_score,
                    'is_anomaly': is_anomaly,
                    'threshold': 75.0  # Anomaly threshold
                },
                'risk': {
                    'level': risk_level,
                    'explanation': explanation
                }
            }

            logger.info(f"✅ Analysis complete for {ticker}: Anomaly={anomaly_score:.1f}, Risk={risk_level}")
            return result

        except Exception as e:
            logger.error(f"❌ Error analyzing {ticker}: {e}", exc_info=True)
            return None

    def get_batch_analysis(self, tickers: List[str], days_back: int = 365) -> List[Dict]:
        """
        Perform analysis for multiple stocks.
        
        Args:
            tickers: List of stock ticker symbols
            days_back: Number of days of historical data to fetch
            
        Returns:
            List of analysis results (successful analyses only)
        """
        results = []
        
        for ticker in tickers:
            analysis = self.get_stock_analysis(ticker, days_back)
            if analysis:
                results.append(analysis)
            else:
                logger.warning(f"Skipping {ticker} - analysis failed")
        
        logger.info(f"Batch analysis complete: {len(results)}/{len(tickers)} successful")
        return results

    def test_connectivity(self) -> bool:
        """
        Test connectivity to data sources.
        
        Returns:
            True if connectivity is OK, False otherwise
        """
        return self.fetcher.test_connectivity()

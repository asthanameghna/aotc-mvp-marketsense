
import yfinance as yf
import pandas as pd
import logging
import time

logger = logging.getLogger(__name__)

def clean_market_data(df):
    """
    Cleans market data dataframe for analysis.
    """
    if df.empty:
        return df
        
    # 1. Forward Fill: If a stock doesn't trade for a minute, 
    # assume the price is the same as the last minute.
    df.fillna(method='ffill', inplace=True)
    
    # 2. Drop Leftovers: If the start of the dataset has gaps, cut them.
    df.dropna(inplace=True)
    
    # 3. Deduplicate: Remove duplicate timestamps
    df = df[~df.index.duplicated(keep='last')]
    
    return df

class YahooFinanceDataFetcher:
    """
    Handles fetching market data from Yahoo Finance.
    Wrapper around yfinance library.
    """
    def __init__(self):
        self.session = None

    def test_connectivity(self):
        """
        Tests connection to Yahoo Finance API
        """
        try:
            logger.info("Testing Yahoo Finance connectivity...")
            test = yf.Ticker("AAPL")
            hist = test.history(period="1d")
            success = not hist.empty
            if success:
                logger.info("✅ Yahoo Finance connectivity verified")
            else:
                logger.warning("⚠️ Yahoo Finance connectivity test returned empty data")
            return success
        except Exception as e:
            logger.error(f"❌ Yahoo Finance connectivity test failed: {e}")
            return False

    def fetch_multiple_stocks(self, distinct_tickers, days_back=365):
        """
        Fetches historical data for multiple tickers in batch.
        """
        if not distinct_tickers:
            return {}
            
        logger.info(f"Fetching data for {len(distinct_tickers)} tickers...")
        
        # yfinance download for multiple tickers returns a MultiIndex DataFrame
        # We need to flatten it into a dict of DataFrames
        try:
            # For single ticker, don't use group_by to avoid MultiIndex
            if len(distinct_tickers) == 1:
                ticker = distinct_tickers[0]
                data = yf.download(
                    ticker, 
                    period=f"{days_back}d",
                    progress=False
                )
                
                portfolio_data = {}
                if not data.empty:
                    # Flatten MultiIndex columns if present
                    # yfinance returns columns like ('Close', 'AAPL') even for single ticker
                    if isinstance(data.columns, pd.MultiIndex):
                        # Take the first level (column names like 'Close', 'Open', etc.)
                        data.columns = data.columns.get_level_values(0)
                    portfolio_data[ticker] = data
                return portfolio_data
            
            # Multiple tickers
            data = yf.download(
                distinct_tickers, 
                period=f"{days_back}d",
                group_by='ticker',
                threads=True,
                progress=False
            )
            
            portfolio_data = {}
            
            for ticker in distinct_tickers:
                # Extract dataframe for this ticker
                try:
                    ticker_df = data[ticker].copy()
                    if not ticker_df.empty:
                         # Drop rows where all columns are NaN (if any)
                        ticker_df.dropna(how='all', inplace=True)
                        if not ticker_df.empty:
                            portfolio_data[ticker] = ticker_df
                except KeyError:
                    logger.warning(f"No data found for {ticker}")
                    continue
                        
            return portfolio_data
            
        except Exception as e:
            logger.error(f"Batch fetch failed: {e}")
            return {}



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
            test = yf.Ticker("AAPL")
            hist = test.history(period="1d")
            return not hist.empty
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
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
            data = yf.download(
                distinct_tickers, 
                period=f"{days_back}d",
                group_by='ticker',
                threads=True,
                progress=False
            )
            
            portfolio_data = {}
            
            # If only one ticker, yfinance doesn't return MultiIndex
            if len(distinct_tickers) == 1:
                ticker = distinct_tickers[0]
                if not data.empty:
                    portfolio_data[ticker] = data
            else:
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

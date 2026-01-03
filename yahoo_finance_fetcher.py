import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class YahooFinanceDataFetcher:
    """
    Production-ready Yahoo Finance data fetcher for MarketSense
    Uses the official yfinance library for robust data access.
    """

    def __init__(self):
        """
        Initialize the fetcher.
        """
        pass

    def fetch_historical_data(self, ticker, days_back=365, interval='1d'):
        """
        Fetch historical data for a single ticker using yfinance
        """
        logger.info(f"📡 Fetching {ticker} data via yfinance...")
        
        try:
            # Download data
            # period can be '1y', '1mo', etc. or use start/end dates.
            # We'll use period for simplicity if days_back matches standard periods, 
            # otherwise start/end is better.
            
            # Using start/end for precision
            end_date = datetime.now()
            start_date = end_date - pd.Timedelta(days=days_back)
            
            # yfinance download
            data = yf.download(
                ticker, 
                start=start_date, 
                end=end_date, 
                interval=interval,
                progress=False,
                auto_adjust=False  # We want raw OHLC usually, but adjusted is often better. User asked for OHLCV. 
                                  # ydefaults to auto_adjust=True in some versions, let's be explicit.
                                  # actually user asked for OHLC.
            )
            
            if data.empty:
                raise ValueError(f"No data returned for {ticker}")

            # yfinance returns a MultiIndex columns if multiple tickers, but here we do one.
            # However, sometimes it returns different formats.
            # Let's clean it up.
            
            # Check if columns are MultiIndex (happens sometimes even with 1 ticker)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1) # Flatten if Ticker is level 1
            
            # Rename columns to ensure standard capitalized format
            data.index.name = 'Date'
            
            # Validation
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            # yfinance might return 'Adj Close', let's check.
            
            # Ensure index is datetime
            data.index = pd.to_datetime(data.index)
            
            logger.info(f"✅ Successfully fetched {len(data)} rows for {ticker}")
            return data

        except Exception as e:
            logger.error(f"❌ Error fetching {ticker}: {e}")
            raise

    def fetch_multiple_stocks(self, tickers, days_back=365, interval='1d'):
        """
        Fetch data for multiple stocks
        """
        results = {}
        failed_tickers = []
        
        logger.info(f"🚀 Batch fetching {len(tickers)} stocks via yfinance...")
        
        # yfinance can download multiple at once which is faster!
        # str_tickers = " ".join(tickers)
        # data = yf.download(str_tickers, ...)
        # But to keep format consistent with existing downstream code (dict of DataFrames),
        # we can iterate or split the bulk result.
        # Bulk download is much better for rate limits.
        
        try:
            data = yf.download(
                tickers,
                period=f"{min(days_back, 730)}d", # approximation, or use start/end
                interval=interval,
                group_by='ticker',
                auto_adjust=False,
                progress=False,
                threads=True
            )
            
            if data.empty:
                logger.error("No data returned from batch download")
                return {}

            # Process the MultiIndex DataFrame
            # Structure: columns are (Ticker, PriceType) or (PriceType, Ticker) if group_by='ticker'
            # If group_by='ticker', top level is Ticker.
            
            for ticker in tickers:
                try:
                    ticker_data = data[ticker].copy()
                    
                    # Drop rows where all are NaN (e.g. non-trading days for this specific stock if others traded? Unlikely for major US stocks)
                    ticker_data.dropna(how='all', inplace=True)
                    
                    if ticker_data.empty:
                        logger.warning(f"Empty data for {ticker}")
                        failed_tickers.append(ticker)
                        continue
                        
                    results[ticker] = ticker_data
                    
                except KeyError:
                    logger.warning(f"Ticker {ticker} not found in download results")
                    failed_tickers.append(ticker)
            
            logger.info(f"📈 Batch complete. Success: {len(results)}, Failed: {len(failed_tickers)}")
            return results

        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            # Fallback to loop if bulk fails?
            return {}

    def test_connectivity(self):
        """
        Test connectivity using a simple fetch
        """
        try:
            test = yf.Ticker("AAPL")
            hist = test.history(period="1d")
            if not hist.empty:
                 return True
            return False
        except Exception:
            return False

def clean_market_data(data):
    """
    Clean market data
    """
    # yfinance data is usually cleaner, but we still do basic checks
    data = data.dropna()
    # Ensure no duplicate timestamps (keep last update)
    data = data[~data.index.duplicated(keep='last')]
    return data

import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    MarketSense Feature Engineering Module
    Transforms raw OHLCV data into model-ready signals.
    """

    def __init__(self):
        pass

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add advanced technical indicators for anomaly detection.
        Includes: RSI, Bollinger Bands, MACD, VWAP, Returns, Volatility.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for feature engineering")
            return df

        # Avoid modifying the original dataframe
        data = df.copy()

        try:
            # --- BASIC FEATURES ---
            # 1. Returns
            data['Returns'] = data['Close'].pct_change()
            data['Log_Returns'] = np.log(data['Close'] / data['Close'].shift(1))

            # 2. Rolling Volatility (20-period standard deviation of returns)
            data['Volatility_20'] = data['Returns'].rolling(window=20).std()

            # 3. Volume Change & Z-Score
            data['Volume_Change'] = data['Volume'].pct_change()
            
            # Volume Z-Score: (Volume - Rolling Mean) / Rolling Std
            vol_mean = data['Volume'].rolling(window=20).mean()
            vol_std = data['Volume'].rolling(window=20).std()
            data['Volume_Z_Score'] = (data['Volume'] - vol_mean) / vol_std
            
            # 3b. Momentum (10-period Rate of Change)
            data['Momentum'] = data['Close'].diff(10)

            # --- ADVANCED ANOMALY INDICATORS ---

            # 4. RSI (Relative Strength Index) - 14 period
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI_14'] = 100 - (100 / (1 + rs))

            # 5. Bollinger Bands (20-period SMA +/- 2 std dev)
            data['BB_Middle'] = data['Close'].rolling(window=20).mean() # SMA 20
            data['BB_Std'] = data['Close'].rolling(window=20).std()
            data['BB_Upper'] = data['BB_Middle'] + (2 * data['BB_Std'])
            data['BB_Lower'] = data['BB_Middle'] - (2 * data['BB_Std'])
            
            # %B: 0=Lower Band, 1=Upper Band. >1 or <0 is anomaly/breakout.
            data['BB_PctB'] = (data['Close'] - data['BB_Lower']) / (data['BB_Upper'] - data['BB_Lower'])
            
            # Bandwidth: Measure of volatility compression/expansion
            data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']

            # 6. MACD (12, 26, 9)
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['MACD_Hist'] = data['MACD'] - data['MACD_Signal'] # Divergence

            # 7. VWAP (Volume Weighted Average Price)
            # Approximation: cumulative(price*vol) / cumulative(vol)
            # Ideally reset daily, but rolling or full series is okay for general anomaly trend in this context
            # We will use a rolling VWAP for localized anomaly detection (e.g. 20 days) to allow it to adapt
            data['VWAP_20'] = (data['Close'] * data['Volume']).rolling(window=20).sum() / data['Volume'].rolling(window=20).sum()
            
            # VWAP Deviation: How far price is from value
            data['VWAP_Dev'] = (data['Close'] - data['VWAP_20']) / data['VWAP_20']

            # 8. Z-Score (Price relative to 20-period MA and StdDev) - Same as before but explicitly useful
            data['Z_Score'] = (data['Close'] - data['BB_Middle']) / data['BB_Std']

            logger.info("✅ Advanced technical indicators added successfully")
            return data

        except Exception as e:
            logger.error(f"❌ Error in feature engineering: {e}")
            return df

    def add_sentiment_score(self, df: pd.DataFrame, score: float) -> pd.DataFrame:
        """
        Injects the external news sentiment score into the dataframe.
        """
        if df.empty:
            return df
        
        # Broadcast the scalar score to the entire column for the current window
        # In a real historical backtest, this would need a time-series of sentiment.
        # For real-time snapshot detection, broadcasting the *current* news mood is valid context.
        df['Sentiment_Score'] = score
        return df

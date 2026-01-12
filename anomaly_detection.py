import pandas as pd
import numpy as np
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketAnomalyDetector:
    """
    detects rare and unusual market behavior using Unsupervised Learning (Isolation Forest).
    """

    def __init__(self, contamination=0.01):
        """
        :param contamination: The proportion of outliers in the data set (default 1%).
        """
        self.contamination = contamination
        self.model = IsolationForest(
            n_estimators=100, 
            contamination=contamination, 
            random_state=42, 
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.features = [
            'Returns', 
            'Volatility_20', 
            'Volume_Change', 
            'Volume_Z_Score', 
            'Momentum',
            'Sentiment_Score'
        ]

    def train_and_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Trains the model on the historical data and adds an 'Anomaly_Score' column (0-100).
        """
        if df.empty or len(df) < 50:
            logger.warning("Not enough data to train anomaly detector (need >50 rows)")
            return df

        data = df.copy()
        
        # Prepare Feature Matrix
        # Drop NaNs created by rolling windows
        feature_data = data[self.features].dropna()
        
        if feature_data.empty:
             return df

        # Normalize features
        X = self.scaler.fit_transform(feature_data)

        # Train Isolation Forest
        self.model.fit(X)

        # Predict Anomaly Score (decision_function returns negative for outliers, positive for inliers)
        # We want a 0-100 score where 100 is high anomaly.
        # IsolationForest decision_function roughly ranges from -0.5 to 0.5
        raw_scores = self.model.decision_function(X)
        
        # Normalize to 0-100
        # Lower decision function = More Anomalous.
        # So we inverse it. 
        # Min-Max Scaling logic adapted for "Anomalousness"
        min_score = raw_scores.min()
        max_score = raw_scores.max()
        
        # Convert to 0-100 score (Higher = More Anomalous)
        # We invert the range: (max - score) / (max - min) * 100
        normalized_scores = ((max_score - raw_scores) / (max_score - min_score)) * 100
        
        # Align indices to put back into DataFrame
        data.loc[feature_data.index, 'Anomaly_Score'] = normalized_scores
        
        # Binary Classification (-1 for outlier, 1 for inlier)
        data.loc[feature_data.index, 'Is_Anomaly'] = self.model.predict(X)
        
        # Map -1 to True (Anomaly) and 1 to False (Normal)
        data['Is_Anomaly'] = data['Is_Anomaly'] == -1

        return data

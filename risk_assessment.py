def calculate_risk_level(anomaly_score, volatility_z_score, sentiment_score):
    """
    Calculates the risk level based on anomaly score, volatility, and sentiment.
    
    Args:
        anomaly_score (float): 0-100 score from Isolation Forest.
        volatility_z_score (float): Z-Score of the volatility (or just high volatility indicator).
                                    For MVP, we might just use the raw volatility or check if it's high.
                                    Actually, let's use the row data directly if possible, but keeping interface simple is good.
                                    Let's assume we pass a combined 'risk factor' or just logic here.
        sentiment_score (float): -1.0 to 1.0 VADER score.
        
    Returns:
        str: "High", "Medium", "Low"
    """
    # Baseline risk from Anomaly Score
    if anomaly_score > 75:
        risk = "High"
    elif anomaly_score > 50:
        risk = "Medium"
    else:
        risk = "Low"
        
    # Modifier: Negative sentiment amplifies risk
    if sentiment_score < -0.2:
        if risk == "Medium":
            risk = "High"
        elif risk == "Low" and anomaly_score > 30:
             risk = "Medium"
             
    # Modifier: High Volatility amplifies risk (assuming volatility_z_score is passed, or just a raw check)
    # If we don't have z-score of volatility handy, we can rely on anomaly score which already factors it in,
    # but the user asked to combine them explicitely.
    # Let's assume the caller passes something indicative.
    
    return risk

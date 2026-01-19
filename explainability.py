def generate_explanation(row):
    """
    Generates a human-readable explanation for the anomaly/risk status.
    Infers a 'General Reason' by combining multiple signals.
    
    Args:
        row (pd.Series): A single row of data containing features like Volume, Returns, Z_Score, etc.
    
    Returns:
        str: A text explanation.
    """
    # Extract signals
    vol_z = row.get('Volume_Z_Score', 0)
    returns = row.get('Returns', 0)
    sentiment = row.get('Sentiment_Score', 0)
    momentum = row.get('Momentum', 0)
    
    # 1. Synthesize High-Level General Reason
    general_reason = ""
    
    # Panic Selling: Drop + High Volume + Negative Sentiment
    if returns < -0.02 and vol_z > 1.5 and sentiment < -0.1:
        general_reason = "Panic selling driven by negative news."
        
    # News Rally: Rise + Positive Sentiment
    elif returns > 0.02 and sentiment > 0.2:
        general_reason = "Rally likely fueled by positive market sentiment."
        
    # Technical Correction: Drop but Neutral/Positive Sentiment (Profit taking)
    elif returns < -0.02 and sentiment >= -0.1:
        general_reason = "Technical correction or profit-taking."
        
    # Volatility Spike: High Volatility but low directional move
    elif row.get('Volatility_20', 0) > 2.0 and abs(returns) < 0.01:
        general_reason = "High uncertainty and volatility without clear direction."
        
    # Heavy Trading / Accumulation: High Volume, Flat Price
    elif vol_z > 2.0 and abs(returns) < 0.01:
        general_reason = "Heavy accumulation or distribution."
        
    # Default fallback
    else:
        # Build component-wise reason if no specific narrative fits
        reasons = []
        if vol_z > 1.5: reasons.append("unusual volume")
        if abs(returns) > 0.03: reasons.append("sharp price action")
        if sentiment < -0.2: reasons.append("negative sentiment")
        elif sentiment > 0.2: reasons.append("positive sentiment")
        
        if reasons:
            general_reason = "Combinations of " + ", ".join(reasons) + "."
        else:
            general_reason = "Normal market fluctuations."
            
    return general_reason

"""
MarketSense Streamlit Frontend
Interactive dashboard for market anomaly detection
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="MarketSense Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# Helper Functions
# ============================================================================

def get_watchlist():
    """Fetch watchlist from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/watchlist")
        if response.status_code == 200:
            return response.json()['tickers']
        return []
    except Exception as e:
        st.error(f"Error fetching watchlist: {e}")
        return []


def get_stock_analysis(ticker):
    """Fetch complete analysis for a ticker."""
    try:
        response = requests.get(f"{API_BASE_URL}/stocks/{ticker}/analysis")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.warning(f"No data available for {ticker}. Background jobs may not have run yet.")
            return None
        else:
            st.error(f"Error fetching data: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None


def get_risk_color(risk_level):
    """Get color for risk level."""
    colors = {
        'Low': 'green',
        'Medium': 'orange',
        'High': 'red'
    }
    return colors.get(risk_level, 'gray')


def get_sentiment_emoji(score):
    """Get emoji for sentiment score."""
    if score > 0.2:
        return "🟢"
    elif score < -0.2:
        return "🔴"
    else:
        return "⚪"


# ============================================================================
# Main Dashboard
# ============================================================================

def main():
    # Header
    st.title("📈 MarketSense Dashboard")
    st.markdown("**AI-Powered Market Anomaly Detection**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Stock selector
        watchlist = get_watchlist()
        if not watchlist:
            st.error("No stocks in watchlist")
            return
        
        selected_ticker = st.selectbox(
            "Select Stock",
            options=watchlist,
            index=0
        )
        
        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.markdown("""
        MarketSense uses machine learning to detect market anomalies by analyzing:
        - Technical indicators
        - News sentiment
        - Price patterns
        - Volume anomalies
        """)
    
    # Fetch data
    with st.spinner(f"Loading data for {selected_ticker}..."):
        data = get_stock_analysis(selected_ticker)
    
    if not data:
        st.info("No data available. Please wait for background jobs to run.")
        return
    
    # Overview Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Current Price",
            value=f"${data['price_data']['close']:.2f}",
            delta=f"{data['price_data']['returns']:.2%}"
        )
    
    with col2:
        anomaly_score = data['anomaly']['score']
        st.metric(
            label="Anomaly Score",
            value=f"{anomaly_score:.1f}/100",
            delta="Anomaly" if data['anomaly']['is_anomaly'] else "Normal",
            delta_color="inverse"
        )
    
    with col3:
        risk_level = data['risk']['level']
        st.markdown(f"**Risk Level**")
        st.markdown(f"<h2 style='color:{get_risk_color(risk_level)}'>{risk_level}</h2>", unsafe_allow_html=True)
    
    with col4:
        sentiment_score = data['sentiment']['score']
        sentiment_emoji = get_sentiment_emoji(sentiment_score)
        st.metric(
            label=f"Sentiment {sentiment_emoji}",
            value=f"{sentiment_score:.3f}",
            delta=f"{data['sentiment']['headline_count']} headlines"
        )
    
    st.markdown("---")
    
    # Technical Indicators
    st.subheader("📊 Technical Indicators")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # RSI Gauge
        fig_rsi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=data['technical_indicators']['rsi_14'],
            title={'text': "RSI (14)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "lightgray"},
                    {'range': [70, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        fig_rsi.update_layout(height=250)
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col2:
        # MACD
        st.markdown("**MACD**")
        st.metric("MACD Line", f"{data['technical_indicators']['macd']:.2f}")
        st.metric("Signal Line", f"{data['technical_indicators']['macd_signal']:.2f}")
    
    with col3:
        # Bollinger Bands
        st.markdown("**Bollinger Bands**")
        st.metric("Upper", f"${data['technical_indicators']['bb_upper']:.2f}")
        st.metric("Middle", f"${data['technical_indicators']['bb_middle']:.2f}")
        st.metric("Lower", f"${data['technical_indicators']['bb_lower']:.2f}")
    
    st.markdown("---")
    
    # Anomaly Detection
    st.subheader("🔍 Anomaly Detection")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Anomaly gauge
        fig_anomaly = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=anomaly_score,
            title={'text': "Anomaly Score"},
            delta={'reference': 75, 'increasing': {'color': "red"}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkred" if anomaly_score > 75 else "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgreen"},
                    {'range': [50, 75], 'color': "lightyellow"},
                    {'range': [75, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))
        fig_anomaly.update_layout(height=300)
        st.plotly_chart(fig_anomaly, use_container_width=True)
    
    with col2:
        st.markdown("**Risk Assessment**")
        st.info(data['risk']['explanation'])
        
        if data['anomaly']['is_anomaly']:
            st.error("⚠️ **ANOMALY DETECTED** - This stock shows unusual market behavior!")
        else:
            st.success("✅ Normal market behavior detected")
    
    st.markdown("---")
    
    # Sentiment Analysis
    st.subheader("📰 News Sentiment")
    
    if data['sentiment']['headline_count'] > 0:
        # Sentiment score display
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.metric(
                "Average Sentiment",
                f"{sentiment_score:.3f}",
                delta=get_sentiment_emoji(sentiment_score)
            )
        
        with col2:
            # Recent headlines
            st.markdown("**Recent Headlines**")
            for headline in data['sentiment']['headlines'][:5]:
                sentiment_emoji = get_sentiment_emoji(headline['sentiment_score'])
                st.markdown(f"{sentiment_emoji} **{headline['title']}** ({headline['source']})")
                st.caption(f"Sentiment: {headline['sentiment_score']:.3f}")
    else:
        st.info("No recent news available")
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {data['timestamp']} | Data source: Yahoo Finance + Google News")


if __name__ == "__main__":
    main()

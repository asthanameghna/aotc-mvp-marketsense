# MarketSense - Financial Intelligence System 📈

MarketSense is a Python-based system that ingests real-time financial market data and news to provide actionable insights. It combines technical analysis (using `yfinance`) with sentiment analysis (using Google News & VADER).

## 🚀 Quick Start

### 1. Setup Environment
Ensure you have Python 3.9+ installed.

```bash
# Create virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Mac/Linux
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Stocks
Edit the `watchlist.txt` file to add the tickers you want to track. One ticker per line.

```text
AAPL
NVDA
TSLA
MSFT
GOOGL
```

### 3. Run Data Ingestion (Market Data)
Fetches OHLC data, calculates technical indicators (RSI, MACD, Bollinger Bands), and checks for anomalies.

**Run Once:**
```bash
python data_ingestion.py
```

**Run in a Loop (Every 15 mins):**
```bash
python data_ingestion.py --loop --interval 900
```

### 4. Run News Ingestion (Sentiment Analysis)
Fetches live news for your watchlist, analyzes sentiment (Positive/Negative/Neutral), and gives a Buy/Sell/Hold verdict.

**Run Once:**
```bash
python news_ingestion.py --interval 0
```

**Run in a Loop (Every 5 mins):**
```bash
python news_ingestion.py --interval 300
```

## 📂 Project Structure

*   `data_ingestion.py`: Main script for stock price data & technical indicators.
*   `news_ingestion.py`: Main script for news fetching & sentiment analysis.
*   `yahoo_finance_fetcher.py`: Handles fetching data from Yahoo Finance.
*   `feature_engineering.py`: Calculates technical indicators.
*   `sentiment_analysis.py`: Uses VADER to score news headlines.
*   `config.py`: Utilities for loading configuration (watchlist).
*   `watchlist.txt`: The requested tickers to track.

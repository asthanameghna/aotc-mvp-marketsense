# MarketSense - AI-Powered Market Anomaly Detection 🧠📈

**MarketSense** is a professional-grade financial intelligence system designed to detect market anomalies in real-time. 
Deployed Link: https://marketsense-v3-verified.onrender.com

Unlike traditional screeners that rely solely on price action, MarketSense employs a **Multi-Modal AI Engine** that fuses **Technical Indicators** (Hard Data) with **News Sentiment Analysis** (Soft Data) to identify statistical outliers, potential crashes, and breakout opportunities.

---

## 🚀 Key Features

*   **Multi-Modal Fusion**: Combines Market Data (Price/Volume) and NLP (News Sentiment) into a single vector.
*   **Unsupervised Learning**: Uses an **Isolation Forest** (ML) model to detect anomalies without needing labeled training data.
*   **Advanced Technicals**: Automatically calculates RSI (14), Bollinger Bands (%B, Bandwidth), MACD, VWAP, and Momentum.
*   **Sentiment Engine**: Scrapes Google News in real-time and computes a VADER sentiment score (-1.0 to +1.0).
*   **Automated Watchlist**: Fully configurable via a simple text file (`watchlist.txt`).

---

## 🛠️ System Architecture

1.  **Ingestion Layer**: 
    *   `yahoo_finance_fetcher.py`: High-performance async data fetching.
    *   `news_ingestion.py`: Real-time news scraping from trusted sources (Reuters, Bloomberg, CNBC).
2.  **Processing Layer**:
    *   `feature_engineering.py`: Computes 10+ technical indicators and injects sentiment scores.
    *   `sentiment_analysis.py`: Uses VADER to quantify the "mood" of the market history.
3.  **Intelligence Layer**:
    *   `anomaly_detection.py`: The core ML brain. Normalizes features and assigns a 0-100 Anomaly Score.
4.  **Orchestrator**:
    *   `data_ingestion.py`: The main loop that ties it all together.

---

## ⚡ Quick Start

### 1. Prerequisites
Ensure you have Python 3.9+ installed.

```bash
# 1. Clone the repository
git clone https://github.com/asthanameghna/aotc-mvp-marketsense.git
cd aotc-mvp-marketsense

# 2. Install Dependencies
pip install -r requirements.txt
```

### 2. Configure Watchlist
Edit `watchlist.txt` in the root directory. Add one stock ticker per line:
```text
AAPL
NVDA
TSLA
MSFT
GOOGL
```

### 3. Run the Anomaly Detector
The system is fully autonomous. Run the main ingestion script to start the analysis.

**Instant Scan (Recommended):**
```bash
python data_ingestion.py
```
*Loads tickers from `watchlist.txt`.*

**Continuous Monitoring (15-min Loop):**
```bash
python data_ingestion.py --loop --interval 900
```

**Ad-Hoc Analysis (Specific Tickers):**
```bash
python data_ingestion.py --tickers AQST VLN
```

---

## 📊 Understanding the Output

The terminal output provides a concise "Head-Up Display" (HUD) for each asset:

```text
📊 AAPL Update:
   Rtn: 0.13% | Z-Score: -1.93 | Momentum: -14.44
   📰 Sentiment: 🟢 +0.26 (Based on 5 headlines)
   🟢 ANOMALY SCORE: 22.4/100 | Detected: False

📊 VLN Update:
   Rtn: 58.97% | Z-Score: 4.02
   📰 Sentiment: ⚪ +0.00 (Neutral)
   🔴 ANOMALY SCORE: 100.0/100 | Detected: True
```

*   **🟢/🔴 Status**: Red indicates a statistical anomaly (Top 1% outlier).
*   **Sentiment**: Positive (+0.2 to +1.0), Neutral (-0.2 to +0.2), Negative (-1.0 to -0.2).
*   **Anomaly Score**: 0 (Normal) to 100 (Extreme Anomaly).

---

## 📝 License
MIT License. Free for educational and research use.

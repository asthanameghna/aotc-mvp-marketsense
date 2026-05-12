# MarketSense - AI-Powered Market Anomaly Detection 🧠📈

### 🚀 **[Access the Live Dashboard Here](https://marketsense-v3-verified.onrender.com)**
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://marketsense-v3-verified.onrender.com)

---

**MarketSense** is a professional-grade financial intelligence system designed to detect market anomalies in real-time. Unlike traditional screeners that rely solely on price action, MarketSense employs a **Multi-Modal AI Engine** that fuses **Technical Indicators** (Hard Data) with **Real-time News Sentiment** (Soft Data) to identify statistical outliers, potential crashes, and breakout opportunities.

For a deep dive into the internal architecture and file structure, see the **[Codebase Overview](CODEBASE_OVERVIEW.md)**.

---

## 📸 Production Proofs
Verified production environment showing real-time AI telemetry and system health.

### 📊 AI-Powered Dashboard
![MarketSense Production Dashboard](docs/images/dashboard_proof.png)

### 🏥 System Health & Database Stats
![MarketSense Health API](docs/images/health_proof.png)

---

## 🚀 Key Features

*   **Multi-Modal Fusion**: Combines Market Data (Price/Volume) and NLP (News Sentiment) into a single analytical vector.
*   **Unsupervised Learning**: Employs an **Isolation Forest** (ML) model to detect anomalies without needing labeled training data.
*   **Anomaly Scoring (0-100)**: Quantifies the "strangeness" of a stock's behavior, making detection objective and scalable.
*   **Advanced Technicals**: Automatically calculates RSI (14), Bollinger Bands (%B, Bandwidth), MACD, VWAP, and Momentum.
*   **Sentiment Engine**: Scrapes Google News in real-time and computes a VADER sentiment score (-1.0 to +1.0).
*   **Risk Assessment**: Automatically categorizes assets into Low, Medium, or High risk buckets based on anomaly scores and volatility.
*   **Automated Background Sync**: Managed scheduler ensures data is always fresh (15-min Market / 5-min News cycles).

---

## 🛠️ System Architecture

1.  **Ingestion Layer**: 
    - `yahoo_finance_fetcher.py`: High-performance async market data fetching.
    - `news_ingestion.py`: Real-time news scraping from trusted global sources.
2.  **Processing Layer**:
    - `feature_engineering.py`: Computes 10+ technical indicators and injects sentiment scores.
    - `sentiment_analysis.py`: Uses VADER to quantify the "mood" of market history.
3.  **Intelligence Layer**:
    - `anomaly_detection.py`: The core ML brain. Normalizes features and assigns a 0-100 Anomaly Score.
4.  **Persistence Layer**:
    - SQLAlchemy-based SQLite database for robust local and production storage.

---

## 💻 Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **ML/Analytics**: Scikit-Learn (Isolation Forest), Pandas, NumPy
- **NLP**: VADER Sentiment Analysis
- **Frontend**: Vanilla JS, Glassmorphism CSS, Dynamic UI Components
- **Infrastructure**: Render.com (Auto-deploy, Background Scheduler)

---

## ⚡ Quick Start (Local)

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/asthanameghna/aotc-mvp-marketsense.git
cd aotc-mvp-marketsense

# Install Dependencies
pip install -r requirements.txt
```

### 2. Run the System
```bash
python main.py
```
*The dashboard will be available at [http://localhost:8000](http://localhost:8000)*

---

## 📝 License
MIT License. Free for educational and research use.
Developed with ❤️ for Advanced Market Intelligence.

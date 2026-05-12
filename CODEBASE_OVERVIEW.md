# MarketSense Codebase Overview 🏗️

This document provides a detailed technical explanation of the MarketSense architecture, modules, and data flow. It is intended for developers looking to understand, maintain, or extend the system.

---

## 🏛️ System Architecture

MarketSense follows a **Modular Monolith** architecture designed for scalability and clear separation of concerns.

### 1. Data Flow Pipeline
The core value of the system is the transformation of raw market data and news into actionable intelligence:
1.  **Ingestion**: Real-time fetching from external APIs (Yahoo Finance, Google News).
2.  **Enrichment**: Calculation of technical indicators and sentiment scores.
3.  **Intelligence**: Machine Learning inference to detect anomalies.
4.  **Persistence**: Storing analyzed results in the database.
5.  **Presentation**: API endpoints serving data to a modern glassmorphic dashboard.

---

## 📂 Core Modules

### 🚀 Application Entry Point
-   **[`main.py`](main.py)**: The FastAPI application entry point. It configures middleware (CORS), initializes the database, starts the background scheduler (APScheduler), and defines the application lifespan.

### 🌐 API Layer (`/api`)
-   **[`routes.py`](api/routes.py)**: Defines all RESTful endpoints.
    -   `GET /api/v1/analysis/{ticker}`: Returns full technical + sentiment analysis.
    -   `GET /api/v1/health`: Returns system health and database statistics.
    -   `POST /api/v1/watchlist`: Updates the active stock monitoring list.
-   **[`models.py`](api/models.py)**: Pydantic models for request validation and response serialization, ensuring strict data contracts.

### 🌍 Data Ingestion & Enrichment
-   **[`data_ingestion.py`](data_ingestion.py)**: The primary orchestrator for standalone or loop-based ingestion.
-   **[`yahoo_finance_fetcher.py`](yahoo_finance_fetcher.py)**: Handles robust communication with the Yahoo Finance API, including retries and data cleaning.
-   **[`news_ingestion.py`](news_ingestion.py)**: Scrapes Headlines and RSS feeds.
-   **[`sentiment_analysis.py`](sentiment_analysis.py)**: Uses the VADER (Valence Aware Dictionary and sEntiment Reasoner) Lexicon to assign sentiment scores to news.

### 🧠 Intelligence & ML
-   **[`feature_engineering.py`](feature_engineering.py)**: Computes advanced indicators:
    -   Bollinger Bands, RSI (14), MACD, Momentum, Z-Scores (Volatility and Volume).
-   **[`anomaly_detection.py`](anomaly_detection.py)**: Implements an **Isolation Forest** model to detect outliers in the feature-sentiment hyperspace.
-   **[`risk_assessment.py`](risk_assessment.py)**: Quantifies risk based on statistical deviations and news sentiment.
-   **[`explainability.py`](explainability.py)**: Translates complex ML scores into human-readable narratives (e.g., "High volatility detected alongside negative news sentiment").

### 💾 Persistence Layer (`/database`)
-   **[`connection.py`](database/connection.py)**: SQLAlchemy engine and session management. Supports SQLite (local) and PostgreSQL (production).
-   **[`models.py`](database/models.py)**: SQL tables for Stocks, MarketData, NewsHeadlines, AnomalyScores, and RiskAssessments.
-   **[`crud.py`](database/crud.py)**: Clean abstraction layer for database operations (Create, Read, Update).

### 🎨 Frontend (`/frontend`)
-   A SPA (Single Page Application) built with vanilla JS and CSS.
-   **[`app.js`](frontend/js/app.js)**: State management and API orchestration.
-   **[`components.js`](frontend/js/components.js)**: Reusable UI elements (Stock cards, status indicators).

---

## ⏰ Background Jobs
Managed in **[`background_jobs.py`](background_jobs.py)**. The system runs two primary concurrent cycles:
1.  **News Sync (5 min)**: Keeps sentiment data fresh.
2.  **Market Sync (15 min)**: Re-calculates indicators and runs ML inference.

---

## ☁️ Deployment Configuration
-   **`render.yaml`**: Infrastructure-as-code for Render.com.
-   **`Procfile`**: Specifies the production web server command.
-   **`requirements.txt`**: Lists all 15+ external Python libraries.

---

## 🛠️ Performance Features
-   **Caching**: `services/cache_service.py` provides an in-memory TTL (Time-To-Live) cache to minimize database load and improve response times.
-   **Lifespan Management**: `main.py` uses FastAPI lifespans to ensure clean startup (DB verification) and shutdown (scheduler termination).

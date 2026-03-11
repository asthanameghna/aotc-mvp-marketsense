/**
 * MarketSense - Main Application
 * Core application logic, API integration, and state management
 */

const App = {
    // Configuration
    config: {
        apiBaseUrl: '/api/v1', // Relative path for deployed environment
        refreshInterval: 30000, // 30 seconds
        autoRefresh: false
    },

    // State
    state: {
        watchlist: [],
        stocksData: {},
        currentModal: null,
        refreshTimer: null,
        historicalData: {},
        chartInterval: 30 // default 30 days
    },

    /**
     * Initialize application
     */
    async init() {
        console.log('🚀 MarketSense initializing...');

        // Setup event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadWatchlist();
        await this.loadDashboard();

        console.log('✅ MarketSense ready');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                if (view) this.switchView(view);
            });
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            Components.showToast('Fetching latest market data...', 'info');
            this.loadDashboard(true);
        });

        // Auto-refresh toggle
        document.getElementById('autoRefresh').addEventListener('change', (e) => {
            this.config.autoRefresh = e.target.checked;
            this.toggleAutoRefresh();
        });

        // Add stock button
        document.getElementById('addStockBtn').addEventListener('click', () => {
            this.switchView('watchlist');
        });

        // Add ticker button
        document.getElementById('addTickerBtn').addEventListener('click', () => {
            this.addToWatchlist();
        });

        // Ticker input enter key
        document.getElementById('tickerInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addToWatchlist();
        });

        // Modal close
        document.getElementById('modalClose').addEventListener('click', () => {
            this.closeStockModal();
        });

        document.getElementById('modalOverlay').addEventListener('click', () => {
            this.closeStockModal();
        });

        // Prevent modal content click from closing
        document.querySelector('.modal-content').addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Time buttons for historical chart
        document.querySelectorAll('.time-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Update active state
                document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');

                // Fetch and render new data
                const days = parseInt(e.target.dataset.days);
                if (this.state.currentModal && !isNaN(days)) {
                    this.state.chartInterval = days;
                    this.fetchAndRenderHistoricalChart(this.state.currentModal, days);
                }
            });
        });
    },

    /**
     * Switch between views
     */
    switchView(viewName) {
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.view === viewName) {
                btn.classList.add('active');
            }
        });

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });

        const targetView = document.getElementById(`${viewName}View`);
        if (targetView) {
            targetView.classList.add('active');
        }

        // Load watchlist items if switching to watchlist view
        if (viewName === 'watchlist') {
            this.renderWatchlistItems();
        }
    },

    /**
     * Toggle auto-refresh
     */
    toggleAutoRefresh() {
        if (this.state.refreshTimer) {
            clearInterval(this.state.refreshTimer);
            this.state.refreshTimer = null;
        }

        if (this.config.autoRefresh) {
            // First run it immediately to get latest data right away
            this.loadDashboard(true);

            // Then set up the interval
            this.state.refreshTimer = setInterval(() => {
                this.loadDashboard(true);
            }, this.config.refreshInterval);
            Components.showToast('Auto-refresh and live data fetching enabled', 'success');
        } else {
            Components.showToast('Auto-refresh disabled', 'info');
        }
    },

    /**
     * Load watchlist from API
     */
    async loadWatchlist() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/watchlist`);
            if (!response.ok) throw new Error('Failed to fetch watchlist');

            const data = await response.json();
            this.state.watchlist = data.tickers || [];

            console.log('📋 Watchlist loaded:', this.state.watchlist);
            return this.state.watchlist;
        } catch (error) {
            console.error('Error loading watchlist:', error);
            Components.showToast('Failed to load watchlist', 'error');
            return [];
        }
    },

    /**
     * Load dashboard data
     */
    async loadDashboard(forceIngest = false) {
        Components.showLoading();

        try {
            // Ensure we have the latest watchlist
            await this.loadWatchlist();

            if (this.state.watchlist.length === 0) {
                Components.showEmpty();
                this.updateStats(0, 0, 0);
                return;
            }

            // Fetch data for all stocks
            const promises = this.state.watchlist.map(ticker =>
                this.fetchStockAnalysis(ticker, forceIngest)
            );

            const results = await Promise.allSettled(promises);

            // Filter successful results
            const stocksData = {};
            let anomalyCount = 0;
            let totalNews = 0;

            results.forEach((result, index) => {
                if (result.status === 'fulfilled' && result.value) {
                    const ticker = this.state.watchlist[index];
                    stocksData[ticker] = result.value;

                    if (result.value.anomaly.is_anomaly) {
                        anomalyCount++;
                    }

                    totalNews += result.value.sentiment.headline_count || 0;
                }
            });

            this.state.stocksData = stocksData;

            // Render stocks
            if (Object.keys(stocksData).length === 0) {
                Components.showEmpty();
            } else {
                this.renderStocks();
                Components.showContent();
            }

            // Update stats
            this.updateStats(
                Object.keys(stocksData).length,
                anomalyCount,
                totalNews
            );

        } catch (error) {
            console.error('Error loading dashboard:', error);
            Components.showError(`Error: ${error.message || error}`);
        }
    },

    /**
     * Fetch stock analysis from API
     */
    async fetchStockAnalysis(ticker, forceIngest = false) {
        try {
            if (forceIngest) {
                // Trigger an ingestion to ensure the database has the latest live data
                await fetch(`${this.config.apiBaseUrl}/stocks/${ticker}/ingest`, { method: 'POST' }).catch(e => console.warn(e));
            }
            const response = await fetch(`${this.config.apiBaseUrl}/stocks/${ticker}/analysis`);

            if (response.status === 404) {
                console.warn(`No data for ${ticker}`);
                return null;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${ticker}:`, error);
            return null;
        }
    },

    /**
     * Render stocks grid
     */
    renderStocks() {
        const grid = document.getElementById('stocksGrid');

        const html = Object.values(this.state.stocksData)
            .map(stock => Components.renderStockCard(stock))
            .join('');

        grid.innerHTML = html;
    },

    /**
     * Update stats
     */
    updateStats(totalStocks, anomalyCount, newsCount) {
        document.getElementById('totalStocks').textContent = totalStocks;
        document.getElementById('anomalyCount').textContent = anomalyCount;
        document.getElementById('newsCount').textContent = newsCount;

        const now = new Date();
        document.getElementById('lastUpdate').textContent =
            now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    },

    /**
     * Open stock detail modal
     */
    async openStockModal(ticker) {
        const data = this.state.stocksData[ticker];
        if (!data) return;

        this.state.currentModal = ticker;

        // Populate modal
        document.getElementById('modalTicker').textContent = ticker;
        document.getElementById('modalTimestamp').textContent =
            new Date(data.timestamp).toLocaleDateString();

        // Render Historical Chart
        // Make sure the requested interval matches the active button
        document.querySelectorAll('.time-btn').forEach(b => {
            b.classList.remove('active');
            if (parseInt(b.dataset.days) === this.state.chartInterval) {
                b.classList.add('active');
            }
        });
        this.fetchAndRenderHistoricalChart(ticker, this.state.chartInterval);

        // Price data
        document.getElementById('modalOpen').textContent = `$${data.price_data.open.toFixed(2)}`;
        document.getElementById('modalHigh').textContent = `$${data.price_data.high.toFixed(2)}`;
        document.getElementById('modalLow').textContent = `$${data.price_data.low.toFixed(2)}`;
        document.getElementById('modalClosePrice').textContent = `$${data.price_data.close.toFixed(2)}`;
        document.getElementById('modalVolume').textContent = data.price_data.volume.toLocaleString();

        const returns = data.price_data.returns || 0;
        const returnsEl = document.getElementById('modalReturns');
        returnsEl.textContent = `${returns >= 0 ? '+' : ''}${(returns * 100).toFixed(2)}%`;
        returnsEl.style.color = returns >= 0 ? '#10b981' : '#ef4444';

        // Anomaly detection
        const anomalyScore = data.anomaly.score;
        Charts.createAnomalyGauge('anomalyGauge', anomalyScore);

        const statusEl = document.getElementById('modalAnomalyStatus');
        if (data.anomaly.is_anomaly) {
            statusEl.textContent = '🔴 Anomaly Detected';
            statusEl.style.color = '#ef4444';
        } else {
            statusEl.textContent = '✅ Normal Behavior';
            statusEl.style.color = '#10b981';
        }

        const riskBadge = document.getElementById('modalRiskBadge');
        const riskClass = data.risk.level.toLowerCase();
        riskBadge.className = `risk-badge ${riskClass}`;
        riskBadge.textContent = `Risk: ${data.risk.level}`;

        // Technical indicators
        const indicators = data.technical_indicators;
        const indicatorsHtml = `
            ${Components.renderIndicator('RSI (14)', indicators.rsi_14 || 0)}
            ${Components.renderIndicator('MACD', indicators.macd || 0, 3)}
            ${Components.renderIndicator('MACD Signal', indicators.macd_signal || 0, 3)}
            ${Components.renderIndicator('BB Upper', indicators.bb_upper || 0)}
            ${Components.renderIndicator('BB Middle', indicators.bb_middle || 0)}
            ${Components.renderIndicator('BB Lower', indicators.bb_lower || 0)}
            ${Components.renderIndicator('BB %B', indicators.bb_pct_b || 0, 3)}
            ${Components.renderIndicator('Volatility (20)', indicators.volatility_20 || 0, 4)}
            ${Components.renderIndicator('Volume Z-Score', indicators.volume_z_score || 0, 2)}
            ${Components.renderIndicator('Momentum', indicators.momentum || 0, 2)}
            ${Components.renderIndicator('Z-Score', indicators.z_score || 0, 2)}
        `;
        document.getElementById('modalIndicators').innerHTML = indicatorsHtml;

        // Sentiment
        const sentimentScore = data.sentiment.score || 0;
        const sentimentEmoji = Components.getSentimentEmoji(sentimentScore);
        const sentimentEl = document.getElementById('modalSentimentScore');
        sentimentEl.innerHTML = `
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                <span style="font-size: 3rem;">${sentimentEmoji}</span>
                <div>
                    <div style="font-size: 2rem; font-weight: 700; font-family: var(--font-mono);">
                        ${sentimentScore.toFixed(3)}
                    </div>
                    <div style="color: var(--color-text-secondary); font-size: 0.875rem;">
                        Based on ${data.sentiment.headline_count} headlines
                    </div>
                </div>
            </div>
        `;

        // Headlines
        const headlinesHtml = data.sentiment.headlines
            .slice(0, 5)
            .map(h => Components.renderHeadline(h))
            .join('');
        document.getElementById('modalHeadlines').innerHTML = headlinesHtml ||
            '<p style="color: var(--color-text-muted);">No recent headlines available</p>';

        // Risk explanation
        document.getElementById('modalExplanation').textContent =
            data.risk.explanation || 'No risk assessment available';

        // Show modal
        document.getElementById('stockModal').classList.add('active');
    },

    /**
     * Fetch and render historical chart
     */
    async fetchAndRenderHistoricalChart(ticker, days) {
        try {
            // Optional: Show loading state in chart area
            const canvas = document.getElementById('historyChart');
            if (canvas && !canvas.chart) {
                // Not strictly necessary but could add visual feedback
            }

            const response = await fetch(`${this.config.apiBaseUrl}/stocks/${ticker}/history?days=${days}`);

            if (!response.ok) {
                console.warn(`Could not fetch historical data for ${ticker}`);
                return;
            }

            const historyData = await response.json();

            if (historyData && historyData.data) {
                Charts.createHistoricalChart('historyChart', historyData.data);
            }
        } catch (error) {
            console.error(`Error fetching history for ${ticker}:`, error);
        }
    },

    /**
     * Close stock detail modal
     */
    closeStockModal() {
        document.getElementById('stockModal').classList.remove('active');
        this.state.currentModal = null;
    },

    /**
     * Add stock to watchlist
     */
    async addToWatchlist() {
        const input = document.getElementById('tickerInput');
        const ticker = input.value.trim().toUpperCase();

        if (!ticker) {
            Components.showToast('Please enter a ticker symbol', 'error');
            return;
        }

        if (this.state.watchlist.includes(ticker)) {
            Components.showToast(`${ticker} is already in watchlist`, 'info');
            input.value = '';
            return;
        }

        try {
            // Step 1: Add to watchlist
            const newWatchlist = [...this.state.watchlist, ticker];

            const watchlistResponse = await fetch(`${this.config.apiBaseUrl}/watchlist`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tickers: newWatchlist })
            });

            if (!watchlistResponse.ok) throw new Error('Failed to update watchlist');

            const watchlistData = await watchlistResponse.json();
            this.state.watchlist = watchlistData.tickers;

            Components.showToast(`✅ ${ticker} added! Fetching data...`, 'success');
            input.value = '';

            this.renderWatchlistItems();

            // Step 2: Trigger immediate data ingestion
            Components.showToast(`⏳ Processing ${ticker} data (this may take 10-15 seconds)...`, 'info');

            try {
                const ingestResponse = await fetch(`${this.config.apiBaseUrl}/stocks/${ticker}/ingest`, {
                    method: 'POST'
                });

                if (ingestResponse.ok) {
                    const ingestData = await ingestResponse.json();
                    Components.showToast(`✅ ${ticker} analysis ready! Anomaly: ${ingestData.anomaly_score.toFixed(1)}, Risk: ${ingestData.risk_level}`, 'success');
                } else {
                    const errorData = await ingestResponse.json();
                    Components.showToast(`⚠️ ${ticker}: ${errorData.detail || 'Data ingestion failed'}`, 'error');
                }
            } catch (ingestError) {
                console.error('Ingestion error:', ingestError);
                Components.showToast(`⚠️ ${ticker}: Could not fetch data. Please check the ticker symbol.`, 'error');
            }

            // Step 3: Switch to dashboard and reload
            this.switchView('dashboard');
            await this.loadDashboard();

            // Step 4: Automatically open the modal for the newly added stock
            setTimeout(async () => {
                if (this.state.stocksData[ticker]) {
                    // Highlight the new stock card
                    const stockCard = document.querySelector(`[data-ticker="${ticker}"]`);
                    if (stockCard) {
                        stockCard.style.animation = 'highlightPulse 2s ease-in-out';
                        stockCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }

                    // Open the modal to show analysis
                    await this.openStockModal(ticker);
                    Components.showToast(`📊 Showing analysis for ${ticker}`, 'info');
                } else {
                    Components.showToast(`⏳ ${ticker} data is being processed. Please refresh in a moment.`, 'info');
                }
            }, 1000);

        } catch (error) {
            console.error('Error adding to watchlist:', error);
            Components.showToast('Failed to add stock', 'error');
        }
    },

    /**
     * Remove stock from watchlist
     */
    async removeFromWatchlist(ticker) {
        try {
            const newWatchlist = this.state.watchlist.filter(t => t !== ticker);

            if (newWatchlist.length === 0) {
                Components.showToast('Watchlist cannot be empty', 'error');
                return;
            }

            const response = await fetch(`${this.config.apiBaseUrl}/watchlist`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tickers: newWatchlist })
            });

            if (!response.ok) throw new Error('Failed to update watchlist');

            const data = await response.json();
            this.state.watchlist = data.tickers;

            Components.showToast(`${ticker} removed from watchlist`, 'success');

            this.renderWatchlistItems();

            // Reload dashboard if on dashboard view
            const dashboardView = document.getElementById('dashboardView');
            if (dashboardView.classList.contains('active')) {
                this.loadDashboard();
            }

        } catch (error) {
            console.error('Error removing from watchlist:', error);
            Components.showToast('Failed to remove stock', 'error');
        }
    },

    /**
     * Render watchlist items
     */
    renderWatchlistItems() {
        const container = document.getElementById('watchlistItems');

        if (this.state.watchlist.length === 0) {
            container.innerHTML = '<p style="color: var(--color-text-muted); text-align: center; padding: 2rem;">No stocks in watchlist</p>';
            return;
        }

        const html = this.state.watchlist
            .map(ticker => Components.renderWatchlistItem(ticker))
            .join('');

        container.innerHTML = html;
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// Export for global access
window.App = App;

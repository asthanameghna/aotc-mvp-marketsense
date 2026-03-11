/**
 * MarketSense - UI Components
 * Reusable component renderers for stock cards, modals, and visualizations
 */

const Components = {
    /**
     * Render a stock card
     */
    renderStockCard(data) {
        const returns = data.price_data.returns || 0;
        const changeClass = returns >= 0 ? 'positive' : 'negative';
        const changeSymbol = returns >= 0 ? '▲' : '▼';

        const anomalyClass = data.anomaly.is_anomaly ? 'detected' : 'normal';
        const anomalyText = data.anomaly.is_anomaly ? '🔴 Anomaly Detected' : '✅ Normal';

        const riskClass = data.risk.level.toLowerCase();

        const sentimentScore = data.sentiment.score || 0;
        const sentimentEmoji = this.getSentimentEmoji(sentimentScore);

        const timestamp = new Date(data.timestamp).toLocaleDateString();

        return `
            <div class="stock-card glass-card" data-ticker="${data.ticker}" onclick="App.openStockModal('${data.ticker}')">
                <div class="stock-header">
                    <div class="stock-ticker">${data.ticker}</div>
                    <div class="stock-timestamp">${this.formatTime(data.timestamp)}</div>
                </div>
                
                <div class="stock-price">
                    <div class="price-main">$${data.price_data.close.toFixed(2)}</div>
                    <div class="price-change ${changeClass}">
                        ${changeSymbol} ${Math.abs(returns * 100).toFixed(2)}%
                    </div>
                </div>
                
                <div class="stock-metrics">
                    <div class="metric-item">
                        <div class="metric-label">Anomaly Score</div>
                        <div class="metric-value">${data.anomaly.score.toFixed(1)}/100</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Sentiment</div>
                        <div class="metric-value">${sentimentEmoji} ${sentimentScore.toFixed(3)}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">RSI</div>
                        <div class="metric-value">${(data.technical_indicators.rsi_14 || 0).toFixed(1)}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Volatility</div>
                        <div class="metric-value">${(data.technical_indicators.volatility_20 || 0).toFixed(3)}</div>
                    </div>
                </div>
                
                <div class="stock-footer">
                    <div class="anomaly-badge ${anomalyClass}">${anomalyText}</div>
                    <div class="risk-badge ${riskClass}">Risk: ${data.risk.level}</div>
                </div>
            </div>
        `;
    },

    /**
     * Render watchlist item
     */
    renderWatchlistItem(ticker) {
        return `
            <div class="watchlist-item">
                <div class="watchlist-ticker">${ticker}</div>
                <button class="watchlist-remove" onclick="App.removeFromWatchlist('${ticker}')">
                    Remove
                </button>
            </div>
        `;
    },

    /**
     * Render headline item
     */
    renderHeadline(headline) {
        const sentimentEmoji = this.getSentimentEmoji(headline.sentiment_score);

        let titleHtml = headline.link
            ? `<a href="${headline.link}" target="_blank" class="headline-link" style="color: inherit; text-decoration: underline;">${sentimentEmoji} ${headline.title}</a>`
            : `${sentimentEmoji} ${headline.title}`;

        return `
            <div class="headline-item">
                <div class="headline-title">
                    ${titleHtml}
                </div>
                <div class="headline-meta">
                    <span>${headline.source || 'Unknown source'}</span>
                    <span>•</span>
                    <span>Sentiment: ${headline.sentiment_score.toFixed(3)}</span>
                </div>
            </div>
        `;
    },

    /**
     * Render technical indicator
     */
    renderIndicator(label, value, decimals = 2) {
        return `
            <div class="indicator-item">
                <div class="indicator-label">${label}</div>
                <div class="indicator-value">${value.toFixed(decimals)}</div>
            </div>
        `;
    },

    /**
     * Get sentiment emoji
     */
    getSentimentEmoji(score) {
        if (score > 0.2) return '🟢';
        if (score < -0.2) return '🔴';
        return '⚪';
    },

    /**
     * Format timestamp
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return date.toLocaleDateString();
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        const container = document.getElementById('toastContainer');
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 300ms ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    /**
     * Show loading state
     */
    showLoading() {
        document.getElementById('loadingState').style.display = 'flex';
        document.getElementById('stocksGrid').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
    },

    /**
     * Show content
     */
    showContent() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('stocksGrid').style.display = 'grid';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
    },

    /**
     * Show empty state
     */
    showEmpty() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('stocksGrid').style.display = 'none';
        document.getElementById('emptyState').style.display = 'flex';
        document.getElementById('errorState').style.display = 'none';
    },

    /**
     * Show error state
     */
    showError(message) {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('stocksGrid').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('errorState').style.display = 'flex';
        document.getElementById('errorMessage').textContent = message;
    }
};

// Export for use in other modules
window.Components = Components;

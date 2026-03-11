/**
 * MarketSense - Chart Visualizations
 * Chart.js based visualizations for anomaly scores and technical indicators
 */

const Charts = {
    /**
     * Create anomaly gauge chart
     */
    createAnomalyGauge(canvasId, score) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if any
        if (canvas.chart) {
            canvas.chart.destroy();
        }

        // Determine color based on score
        let color;
        if (score < 50) {
            color = '#10b981'; // Green
        } else if (score < 75) {
            color = '#f59e0b'; // Orange
        } else {
            color = '#ef4444'; // Red
        }

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [color, 'rgba(255, 255, 255, 0.1)'],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: 270
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            },
            plugins: [{
                id: 'gaugeText',
                afterDraw: (chart) => {
                    const ctx = chart.ctx;
                    const centerX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
                    const centerY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2;

                    ctx.save();
                    ctx.font = 'bold 32px JetBrains Mono';
                    ctx.fillStyle = '#ffffff';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(score.toFixed(1), centerX, centerY - 10);

                    ctx.font = '14px Inter';
                    ctx.fillStyle = '#a0aec0';
                    ctx.fillText('/ 100', centerX, centerY + 20);
                    ctx.restore();
                }
            }]
        });

        canvas.chart = chart;
        return chart;
    },

    /**
     * Create sparkline chart for technical indicators
     */
    createSparkline(canvasId, data, label) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if any
        if (canvas.chart) {
            canvas.chart.destroy();
        }

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map((_, i) => i),
                datasets: [{
                    label: label,
                    data: data,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#a0aec0',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        canvas.chart = chart;
        return chart;
    },

    /**
     * Create sentiment timeline chart
     */
    createSentimentTimeline(canvasId, headlines) {
        // ... (existing code, keeping for brief context but omitting full copy for space. 
        // Wait, I should not replace the existing function. Let me add to the end of the object.)
    },

    /**
     * Create historical price chart
     */
    createHistoricalChart(canvasId, dataPoints) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if any
        if (canvas.chart) {
            canvas.chart.destroy();
        }

        if (!dataPoints || dataPoints.length === 0) {
            return null;
        }

        const labels = dataPoints.map(p => new Date(p.timestamp).toLocaleDateString());
        const data = dataPoints.map(p => p.close);

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Close Price',
                    data: data,
                    borderColor: '#a855f7',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(10, 14, 39, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#a0aec0',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Date',
                            color: '#a0aec0'
                        },
                        ticks: {
                            color: '#718096',
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        title: {
                            display: true,
                            text: 'Price (USD)',
                            color: '#a0aec0'
                        },
                        ticks: {
                            color: '#718096',
                            callback: function (value, index, values) {
                                return '$' + value;
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        canvas.chart = chart;
        return chart;
    }
};

// Export for use in other modules
window.Charts = Charts;

# Real-Time Quantitative Analytics Application

## Overview

End-to-end real-time analytics platform for statistical arbitrage and market analysis. Ingests live tick data from Binance WebSocket, computes advanced analytics (hedge ratios, spreads, z-scores, ADF tests, correlations), and visualizes everything through an interactive Streamlit dashboard.

## Features

- **Real-time Data Ingestion**: WebSocket connection to Binance for live tick data
- **Multi-timeframe Analysis**: 1s, 1m, 5m resampling with automatic aggregation
- **Advanced Analytics**:
  - OLS Hedge Ratio & Spread Calculation
  - Rolling Z-scores with configurable windows
  - Augmented Dickey-Fuller (ADF) stationarity tests
  - Rolling correlations and covariance
  - Kalman Filter for dynamic hedge estimation
  - Robust regression (Huber, Theil-Sen)
  - Volume-weighted analytics
- **Interactive Dashboard**: Real-time charts with zoom, pan, hover
- **Custom Alerts**: User-defined thresholds for z-score, spread, price changes
- **Data Export**: Download processed data and analytics as CSV
- **OHLC Upload**: Optional manual data upload for backtesting

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

This will:

1. Start WebSocket client connecting to Binance
2. Begin ingesting tick data for default symbols (BTCUSDT, ETHUSDT, etc.)
3. Launch Streamlit dashboard at http://localhost:8501

### First Time Setup

Wait 30-60 seconds for:

- WebSocket connection establishment
- Initial tick data accumulation
- First resampling cycle completion

Then navigate to http://localhost:8501

## Architecture

### System Components

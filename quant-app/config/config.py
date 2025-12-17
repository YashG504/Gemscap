"""Configuration settings for the application"""
import os
from typing import List, Dict

class Config:
    """Application configuration"""
    
    # Data Source
    BINANCE_WS_BASE = "wss://stream.binance.com:9443"

    SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
    
    # Resampling intervals (seconds)
    RESAMPLE_INTERVALS = {
        "1s": 1,
        "1m": 60,
        "5m": 300
    }
    
    # Storage
    DB_PATH = "data/ticks.db"
    MAX_TICKS_IN_MEMORY = 1_000_000
    DATA_RETENTION_DAYS = 1
    
    # Analytics
    DEFAULT_ROLLING_WINDOW = 10
    Z_SCORE_WINDOW = 10
    CORRELATION_WINDOW = 50
    ADF_LAG = 1
    
    # Kalman Filter parameters
    KALMAN_TRANSITION_COV = 0.01
    KALMAN_OBSERVATION_COV = 1.0
    
    # Alert settings
    ALERT_CHECK_INTERVAL = 0.5
    ALERT_COOLDOWN = 60
    
    # Dashboard
    DASHBOARD_REFRESH_RATE = 1
    MAX_CHART_POINTS = 1000
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/app.log"
    
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
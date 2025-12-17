"""Data export functionality for CSV downloads"""
import pandas as pd
from io import StringIO
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DataExporter:
    """Handles data export to various formats"""
    
    def __init__(self, data_store, analytics_engine):
        self.data_store = data_store
        self.analytics_engine = analytics_engine
        
    def export_ticks_to_csv(self, symbol: str) -> str:
        """Export raw tick data to CSV string"""
        try:
            df = self.data_store.get_ticks(symbol)
            if df.empty:
                return ""
            
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df[['datetime', 'symbol', 'price', 'quantity']]
            
            return df.to_csv(index=False)
        except Exception as e:
            logger.error(f"Error exporting ticks: {e}")
            return ""
            
    def export_ohlcv_to_csv(self, symbol: str, interval: str) -> str:
        """Export resampled OHLCV data to CSV string"""
        try:
            df = self.data_store.get_resampled_data(symbol, interval)
            if df.empty:
                return ""
            
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'vwap']]
            
            return df.to_csv(index=False)
        except Exception as e:
            logger.error(f"Error exporting OHLCV: {e}")
            return ""
            
    def export_analytics_to_csv(self, symbol1: str, symbol2: str, 
                               interval: str, window: int) -> str:
        """Export complete analytics to CSV string"""
        try:
            # Get hedge ratio
            hedge_ratio = self.analytics_engine.compute_hedge_ratio_ols(
                symbol1, symbol2, interval
            )
            
            if hedge_ratio is None:
                return ""
            
            # Get spread
            spread = self.analytics_engine.compute_spread(
                symbol1, symbol2, interval, hedge_ratio
            )
            
            if spread is None or spread.empty:
                return ""
            
            # Get z-score
            zscore = self.analytics_engine.compute_zscore(spread, window)
            
            # Get correlation
            correlation = self.analytics_engine.compute_rolling_correlation(
                symbol1, symbol2, interval, window
            )
            
            # Combine into DataFrame
            df = pd.DataFrame({
                'timestamp': spread.index,
                'spread': spread.values,
                'zscore': zscore.values if not zscore.empty else None,
                'correlation': correlation.values if correlation is not None else None
            })
            
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df['hedge_ratio'] = hedge_ratio
            df['symbol1'] = symbol1
            df['symbol2'] = symbol2
            df['interval'] = interval
            
            df = df[['datetime', 'symbol1', 'symbol2', 'hedge_ratio', 
                    'spread', 'zscore', 'correlation', 'interval']]
            
            return df.to_csv(index=False)
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return ""
            
    def export_alert_history_to_csv(self, alert_manager) -> str:
        """Export alert history to CSV string"""
        try:
            history = alert_manager.get_recent_history(limit=1000)
            if not history:
                return ""
            
            df = pd.DataFrame(history)
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df[['datetime', 'alert_id', 'condition', 'threshold', 
                    'symbol1', 'symbol2']]
            
            return df.to_csv(index=False)
        except Exception as e:
            logger.error(f"Error exporting alerts: {e}")
            return ""
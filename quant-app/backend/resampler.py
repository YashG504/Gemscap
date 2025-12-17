"""Real-time data resampling to OHLCV format"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DataResampler:
    """Resamples tick data to OHLCV bars"""
    
    def __init__(self, data_store, config):
        self.data_store = data_store
        self.config = config
        self.last_resample_time: Dict[str, Dict[str, float]] = {}
        
    def resample_ticks_to_ohlcv(self, ticks_df: pd.DataFrame, interval_seconds: int) -> pd.DataFrame:
        """Resample ticks to OHLCV format"""
        if ticks_df.empty:
            return pd.DataFrame()
            
        ticks_df = ticks_df.copy()
        ticks_df['timestamp'] = pd.to_datetime(ticks_df['timestamp'], unit='s')
        ticks_df = ticks_df.set_index('timestamp')
        
        # Resample to OHLCV
        resampled = pd.DataFrame()
        resampled['open'] = ticks_df['price'].resample(f'{interval_seconds}S').first()
        resampled['high'] = ticks_df['price'].resample(f'{interval_seconds}S').max()
        resampled['low'] = ticks_df['price'].resample(f'{interval_seconds}S').min()
        resampled['close'] = ticks_df['price'].resample(f'{interval_seconds}S').last()
        resampled['volume'] = ticks_df['quantity'].resample(f'{interval_seconds}S').sum()
        resampled['vwap'] = (
            (ticks_df['price'] * ticks_df['quantity']).resample(f'{interval_seconds}S').sum() /
            ticks_df['quantity'].resample(f'{interval_seconds}S').sum()
        )
        
        resampled = resampled.dropna()
        resampled['timestamp'] = resampled.index.astype(np.int64) // 10**9
        resampled = resampled.reset_index(drop=True)
        
        return resampled
        
    def process_pending_ticks(self):
        """Process and resample pending ticks"""
        symbols = self.data_store.get_available_symbols()
        
        for symbol in symbols:
            for interval_name, interval_seconds in self.config.RESAMPLE_INTERVALS.items():
                try:
                    # Check if enough time has passed
                    if symbol not in self.last_resample_time:
                        self.last_resample_time[symbol] = {}
                        
                    last_time = self.last_resample_time[symbol].get(interval_name, 0)
                    current_time = datetime.now().timestamp()
                    
                    if current_time - last_time < interval_seconds / 2:
                        continue
                        
                    # Get recent ticks
                    ticks_df = self.data_store.get_ticks(symbol, limit=10000)
                    
                    if len(ticks_df) < 2:
                        continue
                        
                    # Resample
                    ohlcv = self.resample_ticks_to_ohlcv(ticks_df, interval_seconds)
                    
                    if not ohlcv.empty:
                        self.data_store.add_resampled_data(symbol, interval_name, ohlcv)
                        self.last_resample_time[symbol][interval_name] = current_time
                        
                except Exception as e:
                    logger.error(f"Resampling error for {symbol} {interval_name}: {e}")
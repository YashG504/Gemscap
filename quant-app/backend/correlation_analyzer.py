"""Cross-correlation analysis and heatmap generation"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class CorrelationAnalyzer:
    """Compute cross-correlation matrices and heatmaps"""
    
    def __init__(self, data_store):
        self.data_store = data_store
        
    def compute_correlation_matrix(self, symbols: List[str], interval: str,
                                   window: int = 50) -> Optional[pd.DataFrame]:
        """Compute rolling correlation matrix for multiple symbols"""
        try:
            # Get price data for all symbols
            price_data = {}
            
            for symbol in symbols:
                df = self.data_store.get_resampled_data(symbol, interval)
                if not df.empty:
                    price_data[symbol] = df.set_index('timestamp')['close']
            
            if len(price_data) < 2:
                return None
            
            # Combine into single DataFrame
            combined = pd.DataFrame(price_data)
            combined = combined.dropna()
            
            if combined.empty:
                return None
            
            # Compute correlation matrix
            corr_matrix = combined.corr()
            
            return corr_matrix
            
        except Exception as e:
            logger.error(f"Correlation matrix error: {e}")
            return None
            
    def compute_rolling_correlation_matrix(self, symbols: List[str], 
                                          interval: str, window: int = 50) -> Optional[Dict]:
        """Compute time-varying correlation matrices"""
        try:
            # Get price data
            price_data = {}
            
            for symbol in symbols:
                df = self.data_store.get_resampled_data(symbol, interval)
                if not df.empty:
                    price_data[symbol] = df.set_index('timestamp')['close']
            
            if len(price_data) < 2:
                return None
            
            # Combine
            combined = pd.DataFrame(price_data)
            combined = combined.dropna()
            
            if len(combined) < window:
                return None
            
            # Compute rolling correlations
            rolling_corrs = []
            timestamps = []
            
            for i in range(window, len(combined)):
                window_data = combined.iloc[i-window:i]
                corr = window_data.corr()
                rolling_corrs.append(corr)
                timestamps.append(combined.index[i])
            
            return {
                'timestamps': timestamps,
                'matrices': rolling_corrs,
                'symbols': list(combined.columns)
            }
            
        except Exception as e:
            logger.error(f"Rolling correlation error: {e}")
            return None
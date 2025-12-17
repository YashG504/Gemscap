"""Analytics computation engine"""
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from sklearn.linear_model import HuberRegressor, TheilSenRegressor
from pykalman import KalmanFilter
from typing import Tuple, Optional, Dict
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AnalyticsEngine:
    """Computes quantitative analytics on price data"""
    
    def __init__(self, data_store, config):
        self.data_store = data_store
        self.config = config
        
    def compute_hedge_ratio_ols(self, symbol1: str, symbol2: str, interval: str) -> Optional[float]:
        """Compute hedge ratio using OLS regression"""
        try:
            df1 = self.data_store.get_resampled_data(symbol1, interval)
            df2 = self.data_store.get_resampled_data(symbol2, interval)
            
            if df1.empty or df2.empty:
                return None
                
            # Merge on timestamp
            merged = pd.merge(df1[['timestamp', 'close']], 
                            df2[['timestamp', 'close']], 
                            on='timestamp', 
                            suffixes=('_1', '_2'))
            
            if len(merged) < 2:
                return None
                
            X = merged['close_2'].values.reshape(-1, 1)
            y = merged['close_1'].values
            
            # OLS: y = beta * X
            beta = np.cov(y, merged['close_2'].values)[0, 1] / np.var(merged['close_2'].values)
            
            return float(beta)
            
        except Exception as e:
            logger.error(f"OLS hedge ratio error: {e}")
            return None
            
    def compute_hedge_ratio_kalman(self, symbol1: str, symbol2: str, interval: str) -> Optional[pd.Series]:
        """Compute dynamic hedge ratio using Kalman Filter"""
        try:
            df1 = self.data_store.get_resampled_data(symbol1, interval)
            df2 = self.data_store.get_resampled_data(symbol2, interval)
            
            if df1.empty or df2.empty:
                return None
                
            merged = pd.merge(df1[['timestamp', 'close']], 
                            df2[['timestamp', 'close']], 
                            on='timestamp', 
                            suffixes=('_1', '_2'))
            
            if len(merged) < 10:
                return None
                
            # Kalman Filter setup
            delta = 1e-5
            trans_cov = delta / (1 - delta) * np.eye(2)
            
            obs_mat = np.vstack([merged['close_2'].values, 
                                np.ones(len(merged))]).T[:, np.newaxis]
            
            kf = KalmanFilter(
                n_dim_obs=1,
                n_dim_state=2,
                initial_state_mean=np.zeros(2),
                initial_state_covariance=np.ones((2, 2)),
                transition_matrices=np.eye(2),
                observation_matrices=obs_mat,
                observation_covariance=1.0,
                transition_covariance=trans_cov
            )
            
            state_means, _ = kf.filter(merged['close_1'].values)
            hedge_ratios = pd.Series(state_means[:, 0], index=merged.index)
            
            return hedge_ratios
            
        except Exception as e:
            logger.error(f"Kalman hedge ratio error: {e}")
            return None
            
    def compute_hedge_ratio_robust(self, symbol1: str, symbol2: str, interval: str, method: str = 'huber') -> Optional[float]:
        """Compute hedge ratio using robust regression"""
        try:
            df1 = self.data_store.get_resampled_data(symbol1, interval)
            df2 = self.data_store.get_resampled_data(symbol2, interval)
            
            if df1.empty or df2.empty:
                return None
                
            merged = pd.merge(df1[['timestamp', 'close']], 
                            df2[['timestamp', 'close']], 
                            on='timestamp', 
                            suffixes=('_1', '_2'))
            
            if len(merged) < 5:
                return None
                
            X = merged['close_2'].values.reshape(-1, 1)
            y = merged['close_1'].values
            
            if method == 'huber':
                reg = HuberRegressor()
            else:  # theil-sen
                reg = TheilSenRegressor()
                
            reg.fit(X, y)
            return float(reg.coef_[0])
            
        except Exception as e:
            logger.error(f"Robust regression error: {e}")
            return None
            
    def compute_spread(self, symbol1: str, symbol2: str, interval: str, hedge_ratio: float) -> Optional[pd.Series]:
        """Compute spread = symbol1 - hedge_ratio * symbol2"""
        try:
            df1 = self.data_store.get_resampled_data(symbol1, interval)
            df2 = self.data_store.get_resampled_data(symbol2, interval)
            
            if df1.empty or df2.empty:
                return None
                
            merged = pd.merge(df1[['timestamp', 'close']], 
                            df2[['timestamp', 'close']], 
                            on='timestamp', 
                            suffixes=('_1', '_2'))
            
            spread = merged['close_1'] - hedge_ratio * merged['close_2']
            spread.index = merged['timestamp']
            
            return spread
            
        except Exception as e:
            logger.error(f"Spread computation error: {e}")
            return None
            
    def compute_zscore(self, spread: pd.Series, window: int) -> pd.Series:
        """Compute rolling z-score of spread"""
        rolling_mean = spread.rolling(window=window, min_periods=1).mean()
        rolling_std = spread.rolling(window=window, min_periods=1).std()
        zscore = (spread - rolling_mean) / rolling_std
        return zscore
        
    def compute_adf_test(self, spread: pd.Series) -> Dict[str, float]:
        """Perform Augmented Dickey-Fuller test"""
        try:
            result = adfuller(spread.dropna(), maxlag=self.config.ADF_LAG)
            return {
                'adf_statistic': result[0],
                'p_value': result[1],
                'critical_1': result[4]['1%'],
                'critical_5': result[4]['5%'],
                'critical_10': result[4]['10%']
            }
        except Exception as e:
            logger.error(f"ADF test error: {e}")
            return {}
            
    def compute_rolling_correlation(self, symbol1: str, symbol2: str, interval: str, window: int) -> Optional[pd.Series]:
        """Compute rolling correlation between two symbols"""
        try:
            df1 = self.data_store.get_resampled_data(symbol1, interval)
            df2 = self.data_store.get_resampled_data(symbol2, interval)
            
            if df1.empty or df2.empty:
                return None
                
            merged = pd.merge(df1[['timestamp', 'close']], 
                            df2[['timestamp', 'close']], 
                            on='timestamp', 
                            suffixes=('_1', '_2'))
            
            corr = merged['close_1'].rolling(window=window).corr(merged['close_2'])
            corr.index = merged['timestamp']
            
            return corr
            
        except Exception as e:
            logger.error(f"Correlation error: {e}")
            return None
            
    def compute_price_statistics(self, symbol: str, interval: str) -> Dict:
        """Compute basic price statistics"""
        try:
            df = self.data_store.get_resampled_data(symbol, interval)
            
            if df.empty:
                return {}
                
            return {
                'current_price': df['close'].iloc[-1],
                'mean_price': df['close'].mean(),
                'std_price': df['close'].std(),
                'min_price': df['close'].min(),
                'max_price': df['close'].max(),
                'total_volume': df['volume'].sum(),
                'num_bars': len(df)
            }
        except Exception as e:
            logger.error(f"Price stats error: {e}")
            return {}
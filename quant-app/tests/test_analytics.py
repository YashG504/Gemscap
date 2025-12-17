"""Unit tests for analytics engine"""
import pytest
import pandas as pd
import numpy as np
from backend.analytics_engine import AnalyticsEngine
from backend.data_store import DataStore
from config.config import Config

@pytest.fixture
def setup():
    config = Config()
    data_store = DataStore(config)
    analytics = AnalyticsEngine(data_store, config)
    return data_store, analytics

def test_hedge_ratio_ols(setup):
    """Test OLS hedge ratio calculation"""
    data_store, analytics = setup
    
    # Create synthetic data
    timestamps = np.arange(100)
    prices1 = 100 + np.random.randn(100).cumsum()
    prices2 = 50 + 0.5 * prices1 + np.random.randn(100) * 2
    
    df1 = pd.DataFrame({
        'timestamp': timestamps,
        'close': prices1
    })
    df2 = pd.DataFrame({
        'timestamp': timestamps,
        'close': prices2
    })
    
    data_store.add_resampled_data('TEST1', '1m', df1)
    data_store.add_resampled_data('TEST2', '1m', df2)
    
    hedge_ratio = analytics.compute_hedge_ratio_ols('TEST1', 'TEST2', '1m')
    
    assert hedge_ratio is not None
    assert isinstance(hedge_ratio, float)
    assert 0.3 < hedge_ratio < 0.7  # Expect around 0.5

def test_zscore_calculation(setup):
    """Test z-score computation"""
    _, analytics = setup
    
    spread = pd.Series(np.random.randn(100))
    zscore = analytics.compute_zscore(spread, window=20)
    
    assert len(zscore) == len(spread)
    assert not zscore.isna().all()

if __name__ == "__main__":
    pytest.main([__file__])
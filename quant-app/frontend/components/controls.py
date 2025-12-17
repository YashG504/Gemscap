"""User control components for dashboard"""
import streamlit as st

def render_controls(available_symbols: list, config) -> dict:
    """Render control panel and return selected values"""
    
    if len(available_symbols) < 2:
        st.error("Need at least 2 symbols with data")
        return {
            'symbol1': 'BTCUSDT',
            'symbol2': 'ETHUSDT',
            'interval': '1m',
            'window': 20,
            'regression_type': 'OLS'
        }
    
    # Symbol selection
    symbol1 = st.selectbox(
        "Primary Symbol",
        available_symbols,
        index=0,
        key='symbol1_select'
    )
    
    # Filter out symbol1 from symbol2 options
    symbol2_options = [s for s in available_symbols if s != symbol1]
    symbol2 = st.selectbox(
        "Secondary Symbol",
        symbol2_options,
        index=0 if symbol2_options else None,
        key='symbol2_select'
    )
    
    st.divider()
    
    # Timeframe selection
    interval = st.selectbox(
        "Timeframe",
        options=list(config.RESAMPLE_INTERVALS.keys()),
        index=1,  # Default to 1m
        key='interval_select'
    )
    
    # Rolling window
    window = st.slider(
        "Rolling Window",
        min_value=5,
        max_value=100,
        value=config.DEFAULT_ROLLING_WINDOW,
        step=5,
        key='window_slider'
    )
    
    # Regression type
    regression_type = st.selectbox(
        "Regression Method",
        options=['OLS', 'Kalman', 'Huber', 'Theil-Sen'],
        index=0,
        key='regression_select'
    )
    
    return {
        'symbol1': symbol1,
        'symbol2': symbol2,
        'interval': interval,
        'window': window,
        'regression_type': regression_type
    }
"""Alert configuration and monitoring panel"""
import streamlit as st
from backend.alert_manager import Alert
import uuid
import pandas as pd

def render_alerts_panel(alert_manager, available_symbols: list, default_interval: str):
    """Render alert configuration panel"""
    
    st.subheader("🔔 Alert Configuration")
    
    # Create new alert
    with st.expander("➕ Create New Alert", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            alert_symbol1 = st.selectbox(
                "Primary Symbol",
                available_symbols,
                key='alert_symbol1'
            )
            
            alert_condition = st.selectbox(
                "Condition",
                ['zscore_above', 'zscore_below', 'zscore_abs_above', 
                 'spread_above', 'spread_below'],
                key='alert_condition'
            )
        
        with col2:
            symbol2_options = [s for s in available_symbols if s != alert_symbol1]
            alert_symbol2 = st.selectbox(
                "Secondary Symbol",
                symbol2_options,
                key='alert_symbol2'
            )
            
            alert_threshold = st.number_input(
                "Threshold",
                value=2.0,
                step=0.1,
                key='alert_threshold'
            )
        
        if st.button("Create Alert", key='create_alert_btn'):
            alert_id = str(uuid.uuid4())[:8]
            new_alert = Alert(
                alert_id=alert_id,
                condition=alert_condition,
                threshold=alert_threshold,
                symbol1=alert_symbol1,
                symbol2=alert_symbol2,
                interval=default_interval
            )
            alert_manager.add_alert(new_alert)
            st.success(f"✓ Alert created: {alert_condition} threshold={alert_threshold}")
            st.rerun()
    
    # Display active alerts
    st.subheader("Active Alerts")
    alerts = alert_manager.get_alerts()
    
    if not alerts:
        st.info("No active alerts. Create one above!")
    else:
        # Convert to DataFrame for display
        alerts_df = pd.DataFrame(alerts)
        
        # Display in table with delete buttons
        for idx, alert in enumerate(alerts):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
            
            with col1:
                st.text(f"{alert['symbol1']}/{alert['symbol2']}")
            with col2:
                st.text(alert['condition'])
            with col3:
                st.text(f"Threshold: {alert['threshold']}")
            with col4:
                st.text(f"🔥 {alert['triggered_count']}")
            with col5:
                if st.button("🗑️", key=f"delete_{alert['id']}"):
                    alert_manager.remove_alert(alert['id'])
                    st.success("Alert deleted")
                    st.rerun()
    
    st.divider()
    
    # Alert history
    st.subheader("📜 Recent Alert History")
    history = alert_manager.get_recent_history(limit=10)
    
    if history:
        history_df = pd.DataFrame(history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'], unit='s')
        st.dataframe(
            history_df[['timestamp', 'condition', 'symbol1', 'symbol2', 'threshold']],
            use_container_width=True
        )
    else:
        st.info("No alerts triggered yet")
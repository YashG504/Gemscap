"""
Main Streamlit dashboard for real-time analytics visualization
"""

import streamlit as st
import sys
from pathlib import Path
import time
import sqlite3

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data_store import DataStore
from backend.analytics_engine import AnalyticsEngine
from backend.alert_manager import AlertManager
from config.config import Config
from frontend.components.price_charts import render_price_charts
from frontend.components.analytics_panel import render_analytics_panel
from frontend.components.controls import render_controls
from frontend.components.alerts_panel import render_alerts_panel
from utils.logger import setup_logger

logger = setup_logger(__name__)

# -------------------------------------------------------------------
# Helper (DB-backed symbol discovery – process safe)
# -------------------------------------------------------------------

def get_available_symbols_from_db(db_path: str):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT DISTINCT symbol FROM ticks").fetchall()
    conn.close()
    return [r[0] for r in rows]


# -------------------------------------------------------------------
# Streamlit page config
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Quant Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# Styling
# -------------------------------------------------------------------

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Session initialization
# -------------------------------------------------------------------

if "config" not in st.session_state:
    st.session_state.config = Config()

    # DB-backed DataStore (shared SQLite persistence)
    st.session_state.data_store = DataStore(
        config=st.session_state.config
    )

    st.session_state.analytics_engine = AnalyticsEngine(
        data_store=st.session_state.data_store,
        config=st.session_state.config,
    )

    st.session_state.alert_manager = AlertManager(
        analytics_engine=st.session_state.analytics_engine,
        config=st.session_state.config,
    )

config = st.session_state.config
data_store = st.session_state.data_store
db_path = config.DB_PATH

# -------------------------------------------------------------------
# Header
# -------------------------------------------------------------------

st.markdown(
    '<p class="main-header">📈 Real-Time Quantitative Analytics Dashboard</p>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Controls")

    # IMPORTANT: read symbols from DB, not in-memory
    available_symbols = get_available_symbols_from_db(db_path)

    if len(available_symbols) < 2:
        st.warning("⏳ Waiting for live market data from Binance...")
        st.info(f"Available symbols in DB: {len(available_symbols)}")
        st.stop()

    controls = render_controls(available_symbols, config)

    st.divider()

    st.subheader("📊 Data Status")
    for sym in available_symbols[:5]:
        df = data_store.get_ticks(sym, limit=1000)
        st.text(f"{sym}: {len(df)} ticks")

    st.divider()

    st.subheader("💾 Export")
    if st.button("Download Analytics CSV"):
        st.info("Export functionality can be extended if required")

# -------------------------------------------------------------------
# Main content
# -------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Price Charts", "📊 Analytics", "🔔 Alerts", "📋 Statistics"]
)

with tab1:
    render_price_charts(
        data_store,
        controls["symbol1"],
        controls["symbol2"],
        controls["interval"],
    )

with tab2:
    render_analytics_panel(
        st.session_state.analytics_engine,
        data_store,
        controls,
    )

with tab3:
    render_alerts_panel(
        st.session_state.alert_manager,
        available_symbols,
        controls["interval"],
    )

with tab4:
    st.subheader("Summary Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**{controls['symbol1']}**")
        stats1 = st.session_state.analytics_engine.compute_price_statistics(
            controls["symbol1"], controls["interval"]
        )
        if stats1:
            st.metric("Current Price", f"${stats1['current_price']:.2f}")
            st.metric("Mean Price", f"${stats1['mean_price']:.2f}")
            st.metric("Std Dev", f"${stats1['std_price']:.2f}")
            st.metric("Total Volume", f"{stats1['total_volume']:.2f}")

    with col2:
        st.write(f"**{controls['symbol2']}**")
        stats2 = st.session_state.analytics_engine.compute_price_statistics(
            controls["symbol2"], controls["interval"]
        )
        if stats2:
            st.metric("Current Price", f"${stats2['current_price']:.2f}")
            st.metric("Mean Price", f"${stats2['mean_price']:.2f}")
            st.metric("Std Dev", f"${stats2['std_price']:.2f}")
            st.metric("Total Volume", f"{stats2['total_volume']:.2f}")

# -------------------------------------------------------------------
# Auto-refresh
# -------------------------------------------------------------------

auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
if auto_refresh:
    time.sleep(config.DASHBOARD_REFRESH_RATE)
    st.rerun()

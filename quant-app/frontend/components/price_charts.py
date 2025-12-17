"""
Price chart rendering using DB-backed ticks
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go


def load_ticks_from_db(db_path, symbol, limit=10000):
    conn = sqlite3.connect(db_path)
    query = """
        SELECT timestamp, price, quantity
        FROM ticks
        WHERE symbol = ?
        ORDER BY timestamp ASC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(symbol, limit))
    conn.close()

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    return df


def resample_ticks(df, interval):
    rule_map = {
        "1s": "1S",
        "1m": "1T",
        "5m": "5T",
    }

    rule = rule_map.get(interval)
    if not rule:
        return pd.DataFrame()

    ohlc = (
        df.set_index("timestamp")
        .resample(rule)
        .agg(
            open=("price", "first"),
            high=("price", "max"),
            low=("price", "min"),
            close=("price", "last"),
            volume=("quantity", "sum"),
        )
        .dropna()
        .reset_index()
    )

    return ohlc


def render_price_charts(data_store, symbol1, symbol2, interval):
    st.subheader(f"Price Charts - {interval} timeframe")

    db_path = data_store.config.DB_PATH

    df1 = load_ticks_from_db(db_path, symbol1)
    df2 = load_ticks_from_db(db_path, symbol2)

    if df1.empty or df2.empty:
        st.warning("⏳ Waiting for tick data from Binance...")
        return

    ohlc1 = resample_ticks(df1, interval)
    ohlc2 = resample_ticks(df2, interval)

    if ohlc1.empty or ohlc2.empty:
        st.warning("⏳ Not enough data yet. Waiting for resampled data...")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=ohlc1["timestamp"],
            open=ohlc1["open"],
            high=ohlc1["high"],
            low=ohlc1["low"],
            close=ohlc1["close"],
            name=symbol1,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ohlc2["timestamp"],
            y=ohlc2["close"],
            mode="lines",
            name=f"{symbol2} (close)",
            yaxis="y2",
        )
    )

    fig.update_layout(
        height=600,
        xaxis_title="Time",
        yaxis_title=symbol1,
        yaxis2=dict(
            title=symbol2,
            overlaying="y",
            side="right",
        ),
        legend=dict(orientation="h"),
    )

    st.plotly_chart(fig, use_container_width=True)

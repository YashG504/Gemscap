"""Analytics visualization panel"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def render_analytics_panel(analytics_engine, data_store, controls):
    """Render analytics computations and visualizations"""
    
    symbol1 = controls['symbol1']
    symbol2 = controls['symbol2']
    interval = controls['interval']
    window = controls['window']
    regression_type = controls['regression_type']
    
    st.subheader(f"Pair Analytics: {symbol1} vs {symbol2}")
    
    # Compute hedge ratio
    if regression_type == 'OLS':
        hedge_ratio = analytics_engine.compute_hedge_ratio_ols(symbol1, symbol2, interval)
    elif regression_type == 'Kalman':
        hedge_ratio_series = analytics_engine.compute_hedge_ratio_kalman(symbol1, symbol2, interval)
        hedge_ratio = hedge_ratio_series.iloc[-1] if hedge_ratio_series is not None and not hedge_ratio_series.empty else None
    else:  # Robust
        method = 'huber' if regression_type == 'Huber' else 'theil-sen'
        hedge_ratio = analytics_engine.compute_hedge_ratio_robust(symbol1, symbol2, interval, method)
    
    if hedge_ratio is None:
        st.warning("⏳ Not enough data for analytics. Please wait...")
        return
    
    # Display hedge ratio
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hedge Ratio (β)", f"{hedge_ratio:.4f}")
    
    # Compute spread
    spread = analytics_engine.compute_spread(symbol1, symbol2, interval, hedge_ratio)
    
    if spread is None or spread.empty:
        st.warning("Unable to compute spread")
        return
    
    # Compute z-score
    zscore = analytics_engine.compute_zscore(spread, window)
    
    with col2:
        current_zscore = zscore.iloc[-1] if not zscore.empty else 0
        st.metric("Current Z-Score", f"{current_zscore:.2f}")
    
    with col3:
        current_spread = spread.iloc[-1]
        st.metric("Current Spread", f"{current_spread:.2f}")
    
    # ADF Test
    if st.button("🧪 Run ADF Test"):
        with st.spinner("Running stationarity test..."):
            adf_results = analytics_engine.compute_adf_test(spread)
            
            if adf_results:
                st.write("**Augmented Dickey-Fuller Test Results:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("ADF Statistic", f"{adf_results['adf_statistic']:.4f}")
                    st.metric("P-Value", f"{adf_results['p_value']:.4f}")
                
                with col2:
                    st.write("**Critical Values:**")
                    st.text(f"1%:  {adf_results['critical_1']:.4f}")
                    st.text(f"5%:  {adf_results['critical_5']:.4f}")
                    st.text(f"10%: {adf_results['critical_10']:.4f}")
                
                if adf_results['p_value'] < 0.05:
                    st.success("✓ Spread is stationary (p < 0.05) - Good for pairs trading!")
                else:
                    st.warning("⚠ Spread may not be stationary (p >= 0.05)")
    
    # Spread and Z-Score chart
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Spread', 'Z-Score')
    )
    
    # Spread line
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(spread.index, unit='s'),
            y=spread.values,
            mode='lines',
            name='Spread',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    # Spread mean line
    spread_mean = spread.mean()
    fig.add_hline(y=spread_mean, line_dash="dash", line_color="gray", 
                  annotation_text=f"Mean: {spread_mean:.2f}", row=1, col=1)
    
    # Z-Score line
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(zscore.index, unit='s'),
            y=zscore.values,
            mode='lines',
            name='Z-Score',
            line=dict(color='purple', width=2)
        ),
        row=2, col=1
    )
    
    # Z-Score threshold lines
    fig.add_hline(y=2, line_dash="dash", line_color="red", 
                  annotation_text="Entry (+2σ)", row=2, col=1)
    fig.add_hline(y=-2, line_dash="dash", line_color="red", 
                  annotation_text="Entry (-2σ)", row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="green", 
                  annotation_text="Exit (0)", row=2, col=1)
    
    fig.update_layout(
        height=600,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white'
    )
    
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Spread Value", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Rolling correlation
    st.subheader("Rolling Correlation")
    correlation = analytics_engine.compute_rolling_correlation(symbol1, symbol2, interval, window)
    
    if correlation is not None and not correlation.empty:
        fig_corr = go.Figure()
        fig_corr.add_trace(
            go.Scatter(
                x=pd.to_datetime(correlation.index, unit='s'),
                y=correlation.values,
                mode='lines',
                name='Correlation',
                line=dict(color='orange', width=2),
                fill='tozeroy'
            )
        )
        
        fig_corr.update_layout(
            title=f'Rolling Correlation (Window={window})',
            xaxis_title='Time',
            yaxis_title='Correlation Coefficient',
            height=300,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
        
        current_corr = correlation.iloc[-1]
        st.info(f"📊 Current Correlation: **{current_corr:.3f}**")

        # ADD TO END OF FILE

def render_backtest_section(analytics_engine, data_store, controls):
    """Render backtesting section"""
    st.subheader("🔄 Mean-Reversion Backtest")
    
    st.info("Test simple mean-reversion strategy: Enter when |z| > threshold, exit when z → 0")
    
    col1, col2 = st.columns(2)
    with col1:
        entry_threshold = st.number_input("Entry Threshold (Z-Score)", value=2.0, step=0.1)
    with col2:
        exit_threshold = st.number_input("Exit Threshold (Z-Score)", value=0.0, step=0.1)
    
    if st.button("🚀 Run Backtest"):
        from backend.backtester import MeanReversionBacktester
        
        with st.spinner("Running backtest..."):
            backtester = MeanReversionBacktester(analytics_engine, data_store)
            results = backtester.run_backtest(
                controls['symbol1'],
                controls['symbol2'],
                controls['interval'],
                controls['window'],
                entry_threshold,
                exit_threshold
            )
            
            if results:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Trades", results['total_trades'])
                    st.metric("Win Rate", f"{results['win_rate']:.1%}")
                
                with col2:
                    st.metric("Total P&L", f"${results['total_pnl']:.2f}",
                             delta=f"Avg: ${results['avg_pnl']:.2f}")
                
                with col3:
                    st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
                
                with col4:
                    st.metric("Max Drawdown", f"${results['max_drawdown']:.2f}")
                
                # Trade history table
                if results['trades']:
                    st.write("**Trade History:**")
                    trades_df = pd.DataFrame(results['trades'][:20])  # Show first 20
                    st.dataframe(
                        trades_df[['direction', 'entry_z', 'exit_z', 'pnl']],
                        use_container_width=True
                    )
            else:
                st.warning("Not enough data for backtest")

def render_correlation_heatmap(data_store, available_symbols, interval):
    """Render correlation heatmap"""
    from backend.correlation_analyzer import CorrelationAnalyzer
    
    st.subheader("🔥 Cross-Correlation Heatmap")
    
    # Symbol selection for heatmap
    selected_symbols = st.multiselect(
        "Select symbols for correlation matrix",
        available_symbols,
        default=available_symbols[:4] if len(available_symbols) >= 4 else available_symbols
    )
    
    if len(selected_symbols) >= 2:
        analyzer = CorrelationAnalyzer(data_store)
        corr_matrix = analyzer.compute_correlation_matrix(selected_symbols, interval)
        
        if corr_matrix is not None:
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale='RdBu',
                zmid=0,
                text=corr_matrix.values,
                texttemplate='%{text:.2f}',
                textfont={"size": 10},
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title=f'Correlation Matrix - {interval}',
                xaxis_title='Symbol',
                yaxis_title='Symbol',
                height=500,
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Not enough data for correlation matrix")
    else:
        st.info("Select at least 2 symbols to display correlation heatmap")
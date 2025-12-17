"""Simple mean-reversion backtester for z-score strategies"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MeanReversionBacktester:
    """Backtest simple mean-reversion strategy on z-score"""
    
    def __init__(self, analytics_engine, data_store):
        self.analytics_engine = analytics_engine
        self.data_store = data_store
        
    def run_backtest(self, symbol1: str, symbol2: str, interval: str,
                    window: int, entry_threshold: float = 2.0,
                    exit_threshold: float = 0.0) -> Optional[Dict]:
        """
        Run simple mean-reversion backtest
        
        Strategy:
        - Enter long when z-score < -entry_threshold
        - Enter short when z-score > +entry_threshold
        - Exit when z-score crosses exit_threshold
        
        Returns dict with performance metrics
        """
        try:
            # Get hedge ratio and spread
            hedge_ratio = self.analytics_engine.compute_hedge_ratio_ols(
                symbol1, symbol2, interval
            )
            
            if hedge_ratio is None:
                return None
            
            spread = self.analytics_engine.compute_spread(
                symbol1, symbol2, interval, hedge_ratio
            )
            
            if spread is None or spread.empty:
                return None
            
            # Calculate z-score
            zscore = self.analytics_engine.compute_zscore(spread, window)
            
            if zscore.empty:
                return None
            
            # Run backtest
            positions = []  # 1 = long, -1 = short, 0 = flat
            trades = []
            
            position = 0
            entry_price = 0
            
            for i in range(len(zscore)):
                z = zscore.iloc[i]
                current_spread = spread.iloc[i]
                
                # Entry logic
                if position == 0:
                    if z < -entry_threshold:
                        # Long signal
                        position = 1
                        entry_price = current_spread
                        trades.append({
                            'entry_idx': i,
                            'entry_spread': current_spread,
                            'entry_z': z,
                            'direction': 'LONG'
                        })
                    elif z > entry_threshold:
                        # Short signal
                        position = -1
                        entry_price = current_spread
                        trades.append({
                            'entry_idx': i,
                            'entry_spread': current_spread,
                            'entry_z': z,
                            'direction': 'SHORT'
                        })
                
                # Exit logic
                elif position != 0:
                    exit_signal = False
                    
                    if position == 1 and z >= exit_threshold:
                        # Exit long
                        exit_signal = True
                    elif position == -1 and z <= exit_threshold:
                        # Exit short
                        exit_signal = True
                    
                    if exit_signal:
                        pnl = position * (current_spread - entry_price)
                        trades[-1].update({
                            'exit_idx': i,
                            'exit_spread': current_spread,
                            'exit_z': z,
                            'pnl': pnl
                        })
                        position = 0
                        entry_price = 0
                
                positions.append(position)
            
            # Calculate metrics
            trades_df = pd.DataFrame([t for t in trades if 'pnl' in t])
            
            if trades_df.empty:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'avg_pnl': 0,
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'trades': []
                }
            
            winning_trades = (trades_df['pnl'] > 0).sum()
            losing_trades = (trades_df['pnl'] < 0).sum()
            
            cumulative_pnl = trades_df['pnl'].cumsum()
            max_drawdown = (cumulative_pnl - cumulative_pnl.cummax()).min()
            
            # Simple Sharpe (annualized, assuming returns are in price points)
            returns = trades_df['pnl']
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            results = {
                'total_trades': len(trades_df),
                'winning_trades': int(winning_trades),
                'losing_trades': int(losing_trades),
                'win_rate': float(winning_trades / len(trades_df)) if len(trades_df) > 0 else 0,
                'total_pnl': float(trades_df['pnl'].sum()),
                'avg_pnl': float(trades_df['pnl'].mean()),
                'sharpe_ratio': float(sharpe),
                'max_drawdown': float(max_drawdown),
                'trades': trades_df.to_dict('records'),
                'positions': positions,
                'zscore': zscore.tolist()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Backtest error: {e}", exc_info=True)
            return None
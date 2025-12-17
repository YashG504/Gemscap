"""Alert management and evaluation"""
from typing import List, Dict, Callable
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Alert:
    """Represents a single alert rule"""
    
    def __init__(self, alert_id: str, condition: str, threshold: float, 
                 symbol1: str, symbol2: str = None, interval: str = '1m'):
        self.alert_id = alert_id
        self.condition = condition  # 'zscore_above', 'zscore_below', 'spread_above', etc.
        self.threshold = threshold
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.interval = interval
        self.last_triggered = 0
        self.triggered_count = 0
        
    def to_dict(self) -> Dict:
        return {
            'id': self.alert_id,
            'condition': self.condition,
            'threshold': self.threshold,
            'symbol1': self.symbol1,
            'symbol2': self.symbol2,
            'interval': self.interval,
            'triggered_count': self.triggered_count
        }

class AlertManager:
    """Manages and evaluates alert rules"""
    
    def __init__(self, analytics_engine, config):
        self.analytics_engine = analytics_engine
        self.config = config
        self.alerts: List[Alert] = []
        self.alert_history: List[Dict] = []
        
    def add_alert(self, alert: Alert):
        """Add new alert"""
        self.alerts.append(alert)
        logger.info(f"Alert added: {alert.condition} threshold={alert.threshold}")
        
    def remove_alert(self, alert_id: str):
        """Remove alert by ID"""
        self.alerts = [a for a in self.alerts if a.alert_id != alert_id]
        
    def get_alerts(self) -> List[Dict]:
        """Get all alerts as dictionaries"""
        return [a.to_dict() for a in self.alerts]
        
    def evaluate_alerts(self):
        """Evaluate all active alerts"""
        current_time = datetime.now().timestamp()
        
        for alert in self.alerts:
            # Check cooldown
            if current_time - alert.last_triggered < self.config.ALERT_COOLDOWN:
                continue
                
            triggered = self._evaluate_single_alert(alert)
            
            if triggered:
                alert.last_triggered = current_time
                alert.triggered_count += 1
                
                self.alert_history.append({
                    'timestamp': current_time,
                    'alert_id': alert.alert_id,
                    'condition': alert.condition,
                    'threshold': alert.threshold,
                    'symbol1': alert.symbol1,
                    'symbol2': alert.symbol2
                })
                
                logger.warning(f"ALERT TRIGGERED: {alert.condition} for {alert.symbol1}/{alert.symbol2}")
                
    def _evaluate_single_alert(self, alert: Alert) -> bool:
        """Evaluate single alert condition"""
        try:
            if 'zscore' in alert.condition:
                hedge_ratio = self.analytics_engine.compute_hedge_ratio_ols(
                    alert.symbol1, alert.symbol2, alert.interval
                )
                if hedge_ratio is None:
                    return False
                    
                spread = self.analytics_engine.compute_spread(
                    alert.symbol1, alert.symbol2, alert.interval, hedge_ratio
                )
                if spread is None or spread.empty:
                    return False
                    
                zscore = self.analytics_engine.compute_zscore(
                    spread, self.config.Z_SCORE_WINDOW
                )
                
                if zscore.empty:
                    return False
                    
                current_zscore = zscore.iloc[-1]
                
                if alert.condition == 'zscore_above':
                    return current_zscore > alert.threshold
                elif alert.condition == 'zscore_below':
                    return current_zscore < alert.threshold
                elif alert.condition == 'zscore_abs_above':
                    return abs(current_zscore) > alert.threshold
                    
            elif 'spread' in alert.condition:
                hedge_ratio = self.analytics_engine.compute_hedge_ratio_ols(
                    alert.symbol1, alert.symbol2, alert.interval
                )
                if hedge_ratio is None:
                    return False
                    
                spread = self.analytics_engine.compute_spread(
                    alert.symbol1, alert.symbol2, alert.interval, hedge_ratio
                )
                if spread is None or spread.empty:
                    return False
                    
                current_spread = spread.iloc[-1]
                
                if alert.condition == 'spread_above':
                    return current_spread > alert.threshold
                elif alert.condition == 'spread_below':
                    return current_spread < alert.threshold
                    
        except Exception as e:
            logger.error(f"Alert evaluation error: {e}")
            return False
            
        return False
        
    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """Get recent alert history"""
        return self.alert_history[-limit:]
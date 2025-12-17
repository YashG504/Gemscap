"""Time-series data storage with in-memory and SQLite persistence"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from threading import Lock
from collections import defaultdict, deque
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DataStore:
    """Manages tick and resampled data storage"""
    
    def __init__(self, config):
        self.config = config
        self.lock = Lock()
        
        # In-memory tick storage
        self.ticks: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100000))
        
        # Resampled data storage
        self.resampled: Dict[str, Dict[str, pd.DataFrame]] = defaultdict(dict)
        
        # SQLite for persistence
        self.conn = sqlite3.connect(self.config.DB_PATH, check_same_thread=False)
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite schema"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS ticks (
                    timestamp REAL,
                    symbol TEXT,
                    price REAL,
                    quantity REAL,
                    PRIMARY KEY (timestamp, symbol)
                )
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                ON ticks(symbol, timestamp)
            """)
            
    def add_tick(self, tick: Dict):
        """Add new tick to storage"""
        with self.lock:
            symbol = tick["symbol"]
            self.ticks[symbol].append(tick)
            
            try:
                self.conn.execute(
                    "INSERT OR REPLACE INTO ticks VALUES (?, ?, ?, ?)",
                    (tick["timestamp"], symbol, tick["price"], tick["quantity"])
                )
                self.conn.commit()
            except Exception as e:
                logger.error(f"DB insert error: {e}")
                
    def get_ticks(self, symbol: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Get recent ticks for symbol"""
        with self.lock:
            ticks_list = list(self.ticks[symbol])
            if limit:
                ticks_list = ticks_list[-limit:]
            return pd.DataFrame(ticks_list)
            
    def add_resampled_data(self, symbol: str, interval: str, df: pd.DataFrame):
        """Store resampled OHLCV data"""
        with self.lock:
            if interval not in self.resampled[symbol]:
                self.resampled[symbol][interval] = df
            else:
                existing = self.resampled[symbol][interval]
                combined = pd.concat([existing, df])
                self.resampled[symbol][interval] = combined.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
                
    def get_resampled_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """Get resampled data for symbol and interval"""
        with self.lock:
            return self.resampled[symbol].get(interval, pd.DataFrame())
            
    def get_available_symbols(self) -> List[str]:
        """Get list of symbols with data"""
        with self.lock:
            return [s for s in self.ticks.keys() if len(self.ticks[s]) > 0]
            
    def cleanup_old_data(self):
        """Remove data older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.config.DATA_RETENTION_DAYS)
        cutoff_ts = cutoff.timestamp()
        
        with self.lock:
            for symbol in self.ticks:
                while self.ticks[symbol] and self.ticks[symbol][0]["timestamp"] < cutoff_ts:
                    self.ticks[symbol].popleft()
                    
            self.conn.execute("DELETE FROM ticks WHERE timestamp < ?", (cutoff_ts,))
            self.conn.commit()
            
    def close(self):
        """Close database connection"""
        self.conn.close()
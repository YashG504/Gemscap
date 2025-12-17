"""OHLC file upload and processing"""
import pandas as pd
from io import StringIO
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class OHLCUploader:
    """Handles OHLC data file uploads"""
    
    def __init__(self, data_store):
        self.data_store = data_store
        
    def process_csv_upload(self, file_content: str, symbol: str, 
                          interval: str) -> tuple[bool, str]:
        """Process uploaded CSV file with OHLC data
        
        Expected format:
        timestamp/datetime, open, high, low, close, volume
        """
        try:
            # Try to read CSV
            df = pd.read_csv(StringIO(file_content))
            
            # Validate required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required_cols if col not in df.columns]
            
            if missing:
                return False, f"Missing columns: {missing}"
            
            # Handle timestamp/datetime column
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp']).astype(int) / 10**9
            elif 'datetime' in df.columns:
                df['timestamp'] = pd.to_datetime(df['datetime']).astype(int) / 10**9
            else:
                return False, "Missing 'timestamp' or 'datetime' column"
            
            # Ensure numeric types
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Drop NaN rows
            df = df.dropna(subset=required_cols + ['timestamp'])
            
            if df.empty:
                return False, "No valid data after processing"
            
            # Add VWAP if not present
            if 'vwap' not in df.columns:
                df['vwap'] = df['close']  # Approximation
            
            # Store in data store
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap']]
            self.data_store.add_resampled_data(symbol, interval, df)
            
            logger.info(f"Uploaded {len(df)} OHLC bars for {symbol} at {interval}")
            return True, f"Successfully uploaded {len(df)} bars"
            
        except Exception as e:
            logger.error(f"Upload processing error: {e}")
            return False, f"Error: {str(e)}"
            
    def get_sample_csv_format(self) -> str:
        """Return sample CSV format for user reference"""
        return """datetime,open,high,low,close,volume
2024-01-01 00:00:00,100.0,101.5,99.5,100.5,1000.0
2024-01-01 00:01:00,100.5,102.0,100.0,101.0,1200.0
2024-01-01 00:02:00,101.0,101.5,100.5,101.2,1100.0"""
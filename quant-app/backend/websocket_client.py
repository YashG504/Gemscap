"""WebSocket client for real-time Binance tick data"""
import json
import time
import threading
from typing import List
import websocket
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BinanceWebSocketClient:
    """Connects to Binance WebSocket and streams tick data"""
    
    def __init__(self, symbols: List[str], data_store, config):
        self.symbols = [s.lower() for s in symbols]
        self.data_store = data_store
        self.config = config
        self.ws = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
    def _build_stream_url(self) -> str:
        """Build multi-stream WebSocket URL"""
        streams = [f"{symbol}@trade" for symbol in self.symbols]
        stream_names = "/".join(streams)
        return f"{self.config.BINANCE_WS_BASE}/stream?streams={stream_names}"
        
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            if "data" in data:
                trade = data["data"]
                tick = {
                    "timestamp": trade["T"] / 1000.0,
                    "symbol": trade["s"],
                    "price": float(trade["p"]),
                    "quantity": float(trade["q"])
                }
                self.data_store.add_tick(tick)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        if self.running:
            self._reconnect()
            
    def _on_open(self, ws):
        """Handle WebSocket open"""
        logger.info(f"WebSocket connected for symbols: {self.symbols}")
        self.reconnect_attempts = 0
        
    def _reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = min(60, 2 ** self.reconnect_attempts)
            logger.info(f"Reconnecting in {wait_time}s (attempt {self.reconnect_attempts})")
            time.sleep(wait_time)
            self.start()
        else:
            logger.error("Max reconnection attempts reached")
            self.running = False
            
    def start(self):
        """Start WebSocket connection"""
        self.running = True
        url = self._build_stream_url()
        
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        
    def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws:
            self.ws.close()
            logger.info("WebSocket stopped")
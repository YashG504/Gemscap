"""
Main entry point for Real-Time Quantitative Analytics Application
Starts WebSocket ingestion and launches Streamlit dashboard
"""
import sys
import time
import signal
import threading
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.websocket_client import BinanceWebSocketClient
from backend.data_store import DataStore
from backend.resampler import DataResampler
from backend.analytics_engine import AnalyticsEngine
from backend.alert_manager import AlertManager
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class QuantApp:
    """Main application orchestrator"""
    
    def __init__(self):
        self.config = Config()
        self.running = False
        
        logger.info("Initializing components...")
        self.data_store = DataStore(config=self.config)
        self.resampler = DataResampler(data_store=self.data_store, config=self.config)
        self.analytics_engine = AnalyticsEngine(data_store=self.data_store, config=self.config)
        self.alert_manager = AlertManager(analytics_engine=self.analytics_engine, config=self.config)
        self.ws_client = BinanceWebSocketClient(
            symbols=self.config.SYMBOLS,
            data_store=self.data_store,
            config=self.config
        )
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received. Cleaning up...")
        self.stop()
        sys.exit(0)
        
    def start(self):
        """Start all background services"""
        logger.info("Starting Quant Analytics Application...")
        self.running = True
        
        ws_thread = threading.Thread(target=self.ws_client.start, daemon=True)
        ws_thread.start()
        logger.info("✓ WebSocket client started")
        
        resampler_thread = threading.Thread(target=self._run_resampler, daemon=True)
        resampler_thread.start()
        logger.info("✓ Resampler started")
        
        alert_thread = threading.Thread(target=self._run_alert_manager, daemon=True)
        alert_thread.start()
        logger.info("✓ Alert manager started")
        
        logger.info("All services running. Starting dashboard...")
        
    def _run_resampler(self):
        """Background resampler loop"""
        while self.running:
            try:
                self.resampler.process_pending_ticks()
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Resampler error: {e}", exc_info=True)
                
    def _run_alert_manager(self):
        """Background alert evaluation loop"""
        while self.running:
            try:
                self.alert_manager.evaluate_alerts()
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Alert manager error: {e}", exc_info=True)
                
    def stop(self):
        """Stop all services gracefully"""
        logger.info("Stopping services...")
        self.running = False
        self.ws_client.stop()
        self.data_store.close()
        logger.info("Services stopped")

def main():
    """Main entry point"""
    app = QuantApp()
    app.start()
    
    time.sleep(2)
    
    dashboard_path = Path(__file__).parent / "frontend" / "dashboard.py"
    
    logger.info(f"Launching Streamlit dashboard at {dashboard_path}")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.headless", "true",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        logger.info("Dashboard closed by user")
    finally:
        app.stop()

if __name__ == "__main__":
    main()
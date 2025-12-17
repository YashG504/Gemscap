from backend.websocket_client import BinanceWebSocketClient
from config.config import Config
import time

# Dummy datastore for testing
class DummyStore:
    def add_tick(self, tick):
        pass  # we just want to see ticks printed

symbols = ["BTCUSDT", "ETHUSDT"]
config = Config()

client = BinanceWebSocketClient(
    symbols=symbols,
    data_store=DummyStore(),
    config=config
)

client.start()

# Let it run for 30 seconds
time.sleep(30)
client.stop()

"""
WebSocket diagnostic tool - Test if Binance connection works
Run this BEFORE running the main app to verify connectivity
"""
import websocket
import json
import time

def test_binance_websocket():
    """Test Binance WebSocket connection"""
    
    print("=" * 60)
    print("BINANCE WEBSOCKET DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test URL
    symbols = ["btcusdt", "ethusdt", "bnbusdt"]
    streams = "/".join([f"{s}@trade" for s in symbols])
    url = f"wss://stream.binance.com:9443/stream?streams={streams}"
    
    print(f"\nTest URL: {url}")
    print(f"Testing symbols: {', '.join([s.upper() for s in symbols])}")
    print("\nConnecting...\n")
    
    message_count = 0
    start_time = time.time()
    
    def on_message(ws, message):
        nonlocal message_count
        message_count += 1
        
        try:
            data = json.loads(message)
            if "data" in data:
                trade = data["data"]
                print(f"✓ Message {message_count}: {trade['s']} @ ${float(trade['p']):.2f} (qty: {float(trade['q']):.4f})")
                
                # Stop after 10 messages
                if message_count >= 10:
                    elapsed = time.time() - start_time
                    print(f"\n{'='*60}")
                    print(f"SUCCESS! Received {message_count} messages in {elapsed:.2f} seconds")
                    print(f"Average rate: {message_count/elapsed:.2f} msg/sec")
                    print(f"{'='*60}")
                    print("\n✅ WebSocket is working correctly!")
                    print("You can now run: python app.py")
                    ws.close()
        except Exception as e:
            print(f"❌ Error parsing message: {e}")
    
    def on_error(ws, error):
        print(f"❌ WebSocket Error: {error}")
        print("\nPossible issues:")
        print("1. No internet connection")
        print("2. Binance API is blocked in your region")
        print("3. Firewall blocking WebSocket connections")
        print("4. Corporate network restrictions")
    
    def on_close(ws, close_code, close_msg):
        if message_count < 10:
            print(f"\n⚠ Connection closed early: {close_code} - {close_msg}")
            print(f"Only received {message_count} messages")
        else:
            print("\n✓ Connection closed successfully")
    
    def on_open(ws):
        print("✓ WebSocket connection opened!")
        print("Waiting for messages...\n")
    
    # Create WebSocket
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    
    # Run for 30 seconds max
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        ws.close()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    
    if message_count == 0:
        print("\n" + "="*60)
        print("❌ FAILED: No messages received")
        print("="*60)
        print("\nTroubleshooting steps:")
        print("1. Check internet connection:")
        print("   ping google.com")
        print("\n2. Test if you can reach Binance:")
        print("   curl https://api.binance.com/api/v3/ping")
        print("\n3. Check if WebSocket port 9443 is blocked:")
        print("   telnet stream.binance.com 9443")
        print("\n4. Try a VPN if Binance is restricted in your region")
        return False
    
    return True

if __name__ == "__main__":
    success = test_binance_websocket()
    exit(0 if success else 1)
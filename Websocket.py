import json
from threading import Thread

import websocket
import ccxt
import time
import pandas as pd

Client = ccxt.binance()

cached_data = {
    "open" : [],
    "high" : [],
    "low"  : [],
    "close": [],
    "time" : []
}

keys = [ "open", "high", "low", "close", "time" ]

def set_initial_data():
    global cached_data
    try:
        ohlcv = Client.fetch_ohlcv('BTC/USDT', "1h", limit=96)
        data = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        print(f'Data was fetched successfully!')

        for key in keys:
            cached_data[key] = data[key].tolist()

    except Exception as ex:
        print(f"failed to set initial data!! \n ERROR: {ex}")

def fetch_data():
    return cached_data


def on_message(ws, message):
    data = json.loads(message)
    candlestick = data['k']

    latest_candle = {
        "open": float(candlestick['o']),
        "high": float(candlestick['h']),
        "low": float(candlestick['l']),
        "close": float(candlestick['c']),
        "time": float(candlestick['t']),
        "closed": candlestick['x']  # True when candle is fully closed
    }

    if latest_candle["closed"]:
        for key in keys:
            cached_data[key].append(latest_candle[key])
            cached_data[key].pop(0)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed, {close_status_code}")

def on_open(ws):
    print("WebSocket connected!")

# Binance **Futures** 1h Klines (use stream.binance.com for spot)
url = "wss://stream.binance.com:9443/ws/btcusdt@kline_1h"

ws = websocket.WebSocketApp(
    url,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

# === 4. Run Everything ===
set_initial_data()

def run():
    while True:
        try:
            print("Starting websocket...")
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"Websocket crashed! ERROR: {e}")
        print("Restarting in 5 seconds...")
        time.sleep(5)

def run_websocket():
    t = Thread(target=run)
    t.daemon = True
    t.start()
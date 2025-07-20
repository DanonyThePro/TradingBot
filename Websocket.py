import json
from threading import Thread

import websocket
import ccxt
import time
import pandas as pd

import Debug

Client = ccxt.binance()

cached_data = {
    "open" : [],
    "high" : [],
    "low"  : [],
    "close": [],
    "time" : []
}

keys = [ "open", "high", "low", "close", "time" ]

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

def set_initial_data():
    global cached_data
    try:
        ohlcv = Client.fetch_ohlcv('BTC/USDT', "1h", limit=96)
        data = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        Debug.success(f'Initial data was fetched successfully!')

        for key in keys:
            cached_data[key] = data[key].tolist()

    except Exception as ex:
        Debug.error(f"Failed to set initial data!! \n ERROR: {ex}")

def fetch_data():
    try:
        return {key: pd.Series(cached_data[key]) for key in keys}
    except Exception as e:
        Debug.error(f"FAILED TO FETCH DATA! \n ERROR: {e}")


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
    else:
        for key in keys:
            cached_data[key][-1] = latest_candle[key]

def on_error(ws, error):
    Debug.error("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    Debug.header(f"WebSocket closed, {close_status_code}")

def on_open(ws):
    Debug.success("WebSocket connected!")

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
    global ws
    while True:
        try:
            print("Starting websocket...")
            ws = websocket.WebSocketApp(
                url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            Debug.warning(f"Websocket crashed! ERROR: {e}")
        Debug.header("Restarting in 5 seconds...")
        time.sleep(5)

def run_websocket():
    t = Thread(target=run)
    t.daemon = True
    t.start()
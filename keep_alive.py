import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, render_template, jsonify
from threading import Thread

import os
import ccxt

app = Flask('')

exchange = ccxt.binance()

status_data = {
    "status": "online",
    "symbol": "",
    "Current Price": "0.0",
    "Entry Price": "N/A",
    "Stop Loss": "N/A",
    "Take Profit": "N/A",
    "Balance": "0.0",
    "P&L(%)": "0.0",
    "P&L($)": "0.0",
    "Last Check": "N/A",
}

signals = []

should_update = False

status_lock = threading.Lock()
@app.route('/')
def status():
    with status_lock:
        return render_template('status.html',
                               status=status_data["status"],
                               symbol=status_data["symbol"],
                               current_price=status_data["Current Price"],
                               entry_price=status_data["Entry Price"],
                               stop_loss=status_data["Stop Loss"],
                               take_profit=status_data["Take Profit"],
                               balance=status_data["Balance"],
                               pnl_percent=status_data["P&L(%)"],
                               pnl_dollar=status_data["P&L($)"],
                               last_check=status_data["Last Check"])

@app.route('/reload')
def reload():
    with status_lock:
        response = {
            "Current Price": status_data["Current Price"],
            "Last Check": status_data["Last Check"]
        }
        return jsonify(response)

@app.route('/chart_values')
def fetch_chart_values():
    open_candles, high_candles, low_candles, close_candles, timestamps = get_btc_data()
    response = {
        "timestamps": timestamps,
        "open_candles": open_candles,
        "high_candles": high_candles,
        "low_candles": low_candles,
        "close_candles": close_candles
    }
    return response

@app.route('/signals')
def get_signals():
    _, _, _, _, timestamps = get_btc_data()
    recent_signals = []
    for signal in signals:
        if timestamps[0] < signal["time"] < timestamps[-1]:
            recent_signals.append(signal)

    response = {
        "signals": signals,
        "recent_signals": recent_signals
    }
    return jsonify(response)

def run():
    port = int(os.environ.get("PORT", 5000))
    print(f"Running on port: {port}")
    app.run(host='0.0.0.0', port=port)

def get_last_price():
    global should_update
    last_price = 0.0

    while True:
        try:
            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f'get_last_price() fetched a ticker')
            last_price = ticker['last']
        except Exception as e:
            print(e)

        with status_lock:
            if last_price == 0.0:
                status_data["Current Price"] = "Failed"
            else:
                status_data["Current Price"] = f"{last_price :.2f}"

            status_data["Last Check"] = datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%d/%m %H:%M:%S")
            should_update = True

        time.sleep(60)

def get_btc_data():
    btc_ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=96)

    print(f'get_btc_data() fetched ohlcv')

    open_candles  = [c[1] for c in btc_ohlcv]
    high_candles  = [c[2] for c in btc_ohlcv]
    low_candles   = [c[3] for c in btc_ohlcv]
    close_candles = [c[4] for c in btc_ohlcv]

    timestamps = [round_to_hour(c[0]) for c in btc_ohlcv]

    return open_candles, high_candles, low_candles, close_candles, timestamps

def round_to_hour(dataTime):
    hour_ms = 60 * 60 * 1000
    return (dataTime // hour_ms) * hour_ms

def keep_alive():
    run_thread = Thread(target=run)
    data_thread = Thread(target=get_last_price)

    run_thread.daemon = True
    data_thread.daemon = True

    run_thread.start()
    data_thread.start()
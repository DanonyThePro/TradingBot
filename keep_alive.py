import time

import pandas as pd
import os

from flask import Flask, render_template, jsonify
from threading import Thread
from Websocket import fetch_data

app = Flask('')

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

cached_chart_data = {
    "open" : [],
    "high" : [],
    "low"  : [],
    "close": [],
    "time" : []
}

@app.route('/uptime_only')
def index():
    return 'What are you doing here?'

@app.route('/')
def status():
    return render_template('status.html',
                           status=status_data["status"],
                           symbol=status_data["symbol"],
                           entry_price=status_data["Entry Price"],
                           stop_loss=status_data["Stop Loss"],
                           take_profit=status_data["Take Profit"],
                           balance=status_data["Balance"],
                           pnl_percent=status_data["P&L(%)"],
                           pnl_dollar=status_data["P&L($)"])

@app.route('/chart_values')
def fetch_chart_values():
    response = {
        "timestamps": cached_chart_data["time"],
        "open_candles": cached_chart_data["open"],
        "high_candles": cached_chart_data["high"],
        "low_candles": cached_chart_data["low"],
        "close_candles": cached_chart_data["close"]
    }
    return jsonify(response)

@app.route('/signals')
def get_signals():
    recent_signals = []
    for signal in signals:
        if len(cached_chart_data["time"]) != 0:
            if cached_chart_data["time"][0] < signal["time"] < cached_chart_data["time"][-1]:
                recent_signals.append(signal)

    response = {
        "signals": signals,
        "recent_signals": recent_signals
    }
    return jsonify(response)


def get_btc_data():
    btc_data = fetch_data()

    print(f'get_btc_data() fetched data...')

    open_candles  = [candle_open  for candle_open  in btc_data["open"]]
    high_candles  = [candle_high  for candle_high  in btc_data["high"]]
    low_candles   = [candle_low   for candle_low   in btc_data["low"]]
    close_candles = [candle_close for candle_close in btc_data["close"]]

    timestamps = [round_to_hour(candle_start_time) for candle_start_time in btc_data["time"]]

    return open_candles, high_candles, low_candles, close_candles, timestamps

def update_chart_data():
    while True:
        o, h, l, c, t = get_btc_data()
        cached_chart_data.update({
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "time": t
        })
        waiting_time = time_until_next_hour()
        print("Chart data updated!")
        print(f"waiting {waiting_time} until next chart data update...")
        time.sleep(waiting_time)


def time_until_next_hour():
    now = pd.Timestamp.utcnow()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + pd.Timedelta(hours=1, minutes=1)
    total_seconds = (next_hour - now).total_seconds()
    return total_seconds

def round_to_hour(dataTime):
    hour_ms = 60 * 60 * 1000
    return (dataTime // hour_ms) * hour_ms


def run():
    port = int(os.environ.get("PORT", 5000))
    print(f"Running on port: {port}")
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    run_thread = Thread(target=run)
    btc_data_thread = Thread(target=update_chart_data)

    run_thread.daemon = True
    btc_data_thread.daemon = True

    run_thread.start()
    btc_data_thread.start()
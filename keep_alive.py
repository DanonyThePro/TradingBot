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

def run():
    port = int(os.environ.get("PORT", 5000))
    print(f"Running on port: {port}")
    app.run(host='0.0.0.0', port=port)

def get_prices():
    global should_update
    last_price = 0.0

    while True:
        try:
            ticker = exchange.fetch_ticker('BTC/USDT')
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

        time.sleep(30)

def keep_alive():
    run_thread = Thread(target=run)
    data_thread = Thread(target=get_prices)

    run_thread.daemon = True
    data_thread.daemon = True

    run_thread.start()
    data_thread.start()
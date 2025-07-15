from flask import Flask, render_template
from threading import Thread

import os

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

@app.route('/')
def status():
    return render_template('status.html', status=status_data["status"], symbol=status_data["symbol"], current_price=status_data["Current Price"], entry_price=status_data["Entry Price"], stop_loss=status_data["Stop Loss"], take_profit=status_data["Take Profit"], balance=status_data["Balance"], pnl_percent=status_data["P&L(%)"], pnl_dollar=status_data["P&L($)"], last_check=status_data["Last Check"])

def run():
    port = int(os.environ.get("PORT", 5000))
    print(f"Running on port: {port}")
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
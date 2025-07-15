import time
from zoneinfo import ZoneInfo
from datetime import datetime
from math import floor

import ccxt
import pandas as pd
import pandas_ta as ta
import os

from keep_alive import keep_alive, status_data

api_key = os.getenv("API_KEY")
secret = os.getenv("SECRET_KEY")

if not api_key:
    raise ValueError("API_KEY does not exist!")
if not secret:
    raise ValueError("SECRET_KEY does not exist!")

Client = ccxt.binance({
    'apiKey' : api_key, # your api key/code
    'secret' : secret # your password
})

Client.load_markets()


def fetch_data(symbol):
    try:
        ohlcv = Client.fetch_ohlcv(symbol, "1h", limit=100)
        data = pd.DataFrame(
            ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        data['time'] = pd.to_datetime(data['time'], unit='ms')
        return data
    except Exception as ex:
        print(ex)
        return pd.DataFrame.empty


def fetch_balance(currency):
    balance = Client.fetch_balance({'recvWindow': 60000})
    currency_balance = balance[currency]
    return currency_balance['free']


def RSI(src, length):
    rsi = ta.rsi(src, length)
    return rsi


def SMA(src, length):
    ma = ta.sma(src, length)
    return ma


def get_direction(start_val, end_val):
    return end_val - start_val


def Min(val1, val2):
    if val1 < val2:
        return val1
    else:
        return val2


def round_quantity(qty, precision):
    factor = 10 ** precision
    return floor(qty * factor) / factor


def time_until_next_hour():
    now = pd.Timestamp.utcnow()
    next_hour = now.replace(minute=0, second=0,
                            microsecond=0) + pd.Timedelta(hours=1)
    total_seconds = (next_hour - now).total_seconds()
    return total_seconds


def sleep_until_next_hour(df):
    prev_open = df['open'].iloc[-2]
    time_to_sleep = time_until_next_hour()
    print(f"Sleeping {time_to_sleep} seconds until next candle")
    time.sleep(time_to_sleep)

    while True:
        time.sleep(10)
        df = fetch_data(symbol)
        current_open = df['open'].iloc[-2]

        if prev_open != current_open:
            break

        print("Candle didn't change: waiting 10 seconds")


rsi_length = 14
rsi_oversold = 30
rsi_overbought = 70

risk_per_trade = 10.0 / 100.0  # change when possible (best 10.0%)

sl_percent = 3.0 / 100.0
tp_percent = 45.0 / 100.0

ma_length = 50

symbol = 'BTC/USDT'

base_balance = fetch_balance('USDT')


def main():
    inPosition = False
    entryPrice = 0.0
    stopLoss = 0.0
    takeProfit = 0.0

    while True:
        df = fetch_data(symbol)

        status_data["symbol"] = symbol
        status_data["Current Price"] = f"{df['close'].iloc[-1] :.2f}"
        if entryPrice != 0.0:
            status_data["Entry Price"] = f"{entryPrice :.2f}"
        if stopLoss != 0.0:
            status_data["Stop Loss"] = f"{stopLoss :.2f}"
        if takeProfit != 0.0:
            status_data["Take Profit"] = f"{takeProfit :.2f}"
        status_data["Balance"] = f"{fetch_balance('USDT') :.2f}"
        status_data["P&L(%)"] = f"{(((fetch_balance('USDT') - base_balance) / base_balance) * 100.0) :.2f}"
        status_data["P&L($)"] = f"{fetch_balance('USDT') - base_balance :.2f}"
        status_data["Last Check"] = datetime.now(ZoneInfo("Asia/Jerusalem")).strftime("%d/%m %H:%M:%S")

        print(status_data['Last Check'])

        sleep_until_next_hour(df)

        balance = fetch_balance('USDT')
        close = df['close']

        rsi = RSI(close, rsi_length)

        directionRSI = get_direction(rsi.iloc[-2], rsi.iloc[-1])

        ma = SMA(close, ma_length)
        uptrend = close > ma

        long_condition = (directionRSI < 0 and rsi.iloc[-1] > rsi_overbought
                          and rsi.iloc[-2] > rsi_overbought
                          and close.iloc[-1] < close.iloc[-2] and uptrend
                          and not inPosition)

        exit_condition = ((directionRSI > 0 and rsi.iloc[-1] < rsi_oversold)
                          or (rsi.iloc[-1] < rsi_oversold
                              and rsi.iloc[-2] < rsi_oversold))

        risk_amount = balance * risk_per_trade
        risk_per_share = close.iloc[-1] * sl_percent
        position_size = risk_amount / risk_per_share

        if long_condition:
            entryPrice = close.iloc[-1]
            stopLoss = close.iloc[-1] * (1 - sl_percent)
            takeProfit = close.iloc[-1] * (1 + tp_percent)

            qty = Min(position_size, balance / close.iloc[-1])

            print("📈 BUY SIGNAL!! \n" +
                  f"Quantity: {round_quantity(qty, 5)} \n" +
                  f"Price: ${close.iloc[-1] :.2f}\n" +
                  f"Target: $ {takeProfit :.2f} \n" +
                  f"Stop Loss: ${stopLoss :.2f}")
            Client.create_market_order(symbol, 'buy', round_quantity(qty, 5))
            inPosition = True

        if inPosition:
            if exit_condition:
                print(
                    "🗿 SELL SIGNAL \n" + f"Price: $ {close.iloc[-1] :.2f} \n" +
                    f"Entry: $ {entryPrice :.2f} \n" +
                    f"P&L: {(((close.iloc[-1] - entryPrice) / entryPrice) * 100) :.2f}%"
                )
                Client.create_market_order(symbol, 'sell',
                                           fetch_balance('BTC'))
                inPosition = False

            if close.iloc[-1] < stopLoss:
                print(
                    "🛑 STOP LOSS HIT \n" +
                    f"Price: $ {close.iloc[-1] :.2f} \n" +
                    f"Entry: $ {entryPrice :.2f} \n" +
                    f"Loss: {(((close.iloc[-1] - entryPrice) / entryPrice) * 100) :.2f}%"
                )
                Client.create_market_order(symbol, 'sell',
                                           fetch_balance('BTC'))
                inPosition = False

            if close.iloc[-1] >= takeProfit:
                print(
                    "🤑 TAKE PROFIT HIT \n" +
                    f"Price: $ {close.iloc[-1] :.2f} \n" +
                    f"Entry: $ {entryPrice :.2f} \n" +
                    f"Profit: {(((close.iloc[-1] - entryPrice) / entryPrice) * 100) :.2f}%"
                )
                Client.create_market_order(symbol, 'sell',
                                           fetch_balance('BTC'))
                inPosition = False


if __name__ == '__main__':
    print("Bot is running...")
    keep_alive()
    main()

# populates stock_price table with stock prices

import sqlite3
import numpy
import tulipy
import config
import alpaca_trade_api as tradeapi
from datetime import date

current_date = date.today().isoformat()

connection = sqlite3.connect(config.DB_PATH)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()
cursor.execute("""
    SELECT id, symbol, name FROM stock
""")
rows = cursor.fetchall()
symbols = []
stock_dict = {}
# for each stock symbol, append to array symbols and for each symbol set its value to the its stock id
for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL) # references Alpaca Trade API

chunk_size = 200 # alpaca does not accept API calls over 200

# for each stock in the stock table (grabbing 200 at a time)
for i in range(0, len(symbols), chunk_size):
    symbol_chunk = symbols[i:i+chunk_size] 
    barsets = api.get_barset(symbol_chunk, 'day') # grab bars for 200 symbols

    for symbol in barsets:
        print(f"processing symbol {symbol}")

        recent_closes = [bar.c for bar in barsets[symbol]] # grabs closing price for each bar in the set of bars of a symbol

        for bar in barsets[symbol]:
            stock_id = stock_dict[symbol]

            if len(recent_closes) >= 50 and current_date == bar.t.date().isoformat(): # if we have 50 recent closes recorded, saves 20 day SMA, 50 day SMA and RSI
                sma_20 = tulipy.sma(numpy.array(recent_closes), period=20)[-1]
                sma_50 = tulipy.sma(numpy.array(recent_closes), period=50)[-1]
                rsi_14 = tulipy.rsi(numpy.array(recent_closes), period=14)[-1]

            else:
                sma_20, sma_50, rsi_14 = None, None, None
            # inserts data from Alpaca API about stock and data found (SMA 20, SMA 50, RSI)
            cursor.execute("""
                INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma_20, sma_50, rsi_14)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v, sma_20, sma_50, rsi_14))
connection.commit() # commits changes to sqlite

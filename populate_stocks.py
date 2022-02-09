#populates the stock table with stocks

import sqlite3
import config
import alpaca_trade_api as tradeapi
connection = sqlite3.connect(config.DB_PATH)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()
cursor.execute("""
    SELECT symbol, name FROM stock
""")
rows = cursor.fetchall()
symbols = [row['symbol'] for row in rows]
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL) ## references Alpaca API
assets = api.list_assets()
# if the stock is active, tradable and not already in the stock table
# insert into stock table
for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f"Added a new stock {asset.symbol} {asset.name}")
            cursor.execute(
                "INSERT INTO stock (symbol, name, exchange, shortable) VALUES (?, ?, ?, ?)", (asset.symbol, asset.name, asset.exchange, asset.shortable))
    except Exception as e:
        print(asset.symbol)
        print(e)
connection.commit() # commits changes

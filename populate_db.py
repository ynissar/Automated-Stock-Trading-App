from logging import exception
import sqlite3
import alpaca_trade_api as tradeapi

connection = sqlite3.connect('app.db')

cursor = connection.cursor()

api = tradeapi.REST('PK9TMVELQJLUNOKU12F5', 'lFgHnFIgPB6wX9HQbeI5Ifa4Io4ABtsTKi9vfX2s',
                    base_url='https://paper-api.alpaca.markets')  # or use ENV Vars shown below
assets = api.list_assets()

for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable == True:
            cursor.execute(
                "insert into stock (symbol, company) values (?, ?)", (asset.symbol, asset.name))
    except Exception as e:
        print(asset.symbol)
        print(e)
connection.commit()

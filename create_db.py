# Used to create tables 
# Tables: stocks, stock prices, strategies and stocks with strategies applied to them 

import sqlite3

connection = sqlite3.connect('app.db')

cursor = connection.cursor()

# Creates a table for stocks
cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY, 
        symbol TEXT NOT NULL UNIQUE, 
        name TEXT NOT NULL,
        exchange TEXT NOT NULL,
        shortable BOOLEAN NOT NULL
    )
""")

# Creates a table for stock prices (references stock id)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_price (
        id INTEGER PRIMARY KEY, 
        stock_id INTEGER,
        date NOT NULL,
        open NOT NULL, 
        high NOT NULL, 
        low NOT NULL, 
        close NOT NULL,  
        volume NOT NULL,
        sma_20,
        sma_50,
        rsi_14,
        FOREIGN KEY (stock_id) REFERENCES stock (id)
    )
""")

# Creates a table for strategies
cursor.execute("""
    Create table if not exists strategy (
        id INTEGER PRIMARY KEY,
        name NOT NULL
    )
""")

# Creates a table for stocks with strategies applied to them (references stock id and strategy id)
cursor.execute("""
    Create table if not exists stock_strategy (
        stock_id INTEGER NOT NULL,
        strategy_id INTEGER NOT NULL,
        FOREIGN KEY (stock_id) REFERENCES stock (id)
        FOREIGN KEY (strategy_id) REFERENCES strategy (id)
    )
""")

# two stock strategies
strategies = ['opening_range_breakout', 'opening_range_breakdown']

for strategy in strategies:
    cursor.execute("""
        INSERT INTO strategy (name) VALUES (?)
    """, (strategy,))

# commits changes to sqlite
connection.commit()

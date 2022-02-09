# Uses REST API to create a dynamic website for the user to use to see stocks they can perform strategies on using the Alpaca Trade API
# displays stocks, stocks which the user is currently performing a strategy on and other filters

from fastapi import FastAPI, Request, Form
import sqlite3
from fastapi.responses import RedirectResponse
import config
from fastapi.templating import Jinja2Templates
from datetime import date

app = FastAPI() # REST API used to create a dynamic website
templates = Jinja2Templates(directory="templates") # used to display an HTML page

# default page
# displays all stocks
@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get('filter', False)

    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # if the filter is new_closing_highs
    # displays stocks and displays the maximum close price
    if stock_filter == 'new_closing_highs':
        cursor.execute("""select * from (
	select symbol, name, stock_id, max(close), date
	from stock_price join stock on stock.id = stock_price.stock_id
	group by stock_id
	order by symbol
	) where date = (select max(date) from stock_price) """)
     # displays stocks and displays the minimum close price
    elif stock_filter == 'new_closing_lows':
        cursor.execute("""select * from (
	select symbol, name, stock_id, min(close), date
	from stock_price join stock on stock.id = stock_price.stock_id
	group by stock_id
	order by symbol
	) where date = (select max(date) from stock_price) """)
    else:
        cursor.execute("""
            SELECT id, symbol, name FROM stock order by symbol
        """)

    rows = cursor.fetchall()

    # displays RSI, SMA 20, SMA 50 and close
    cursor.execute("""
        select symbol, rsi_14, sma_20, sma_50, close
        from stock join stock_price on stock_price.stock_id = stock.id
        where date = (select max(date) from stock_price) 
        """)

    indicator_rows = cursor.fetchall()
    indicator_values = {}

    for row in indicator_rows:
        indicator_values[row['symbol']] = row

    # returns index template providing the stock rows and assigning each row to an indicator value (the stocks's symbol)
    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows, "indicator_values": indicator_values})

# when the user is looking at a specific stock
@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM strategy
    """)

    strategies = cursor.fetchall()

    cursor.execute("""
        SELECT id, symbol, name FROM stock where symbol = ? 
    """, (symbol,))

    row = cursor.fetchone()

    cursor.execute("""
        SELECT * from stock_price WHERE stock_id = ? order by date desc
    """, (row['id'],))

    prices = cursor.fetchall()

    # returns html page template for a specific stock with details about it. Provides it with the stock's info, prices and what strategy is being applied
    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock": row, "bars": prices, "strategies": strategies})

# posting a stock onto a strategy
# updates stock_strategy table to reflect the stock being added 
@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    connection = sqlite3.connect(config.DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (?, ?)
    """, (stock_id, strategy_id))

    connection.commit()

    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code=303)

# when the user is viewing the stocks with a strategy currently being applied onto them
@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name
        FROM strategy
        WHERE id = ?
    """, (strategy_id,))

    strategy = cursor.fetchone()

    cursor.execute("""
        SELECT symbol, name 
        FROM stock
        JOIN stock_strategy ON stock_strategy.stock_id = stock.id
        WHERE strategy_id = ?
    """, (strategy_id,))

    stocks = cursor.fetchall()

    return templates.TemplateResponse("strategy.html", {"request": request, "stocks": stocks, "strategy": strategy})

from fastapi import FastAPI, Request
import sqlite3
import config
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    print(dir(request))
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, symbol, name FROM stock order by symbol
    """)

    rows = cursor.fetchall()
    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows})


@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, symbol, name FROM stock where symbol = ? 
    """, (symbol,))

    row = cursor.fetchone()

    cursor.execute("""
        SELECT * from stock_price WHERE stock_id = ? order by date desc
    """, (row['id'],))

    prices = cursor.fetchall()

    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock": row, "bars": prices})

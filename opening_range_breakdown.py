# Applies opening range breakout strategy to stocks in stock_strategy table
# Opening range breakdown strategy explained:
# Opening range breakdown strategy finds the range between the lowest minute bar and highest minute bar in the first 15 min
# It will then short when a minute bar has closed at a price LOWER than the lowest minute bar from the first 15 min
# It will buy when the price of the shares bought reach their (take profit) short price - opening range or (stop loss) short price + opening range

import sqlite3
from sqlite3.dbapi2 import Cursor
from alpaca_trade_api.rest import TimeFrame
import config
import alpaca_trade_api as tradeapi
from datetime import date
import smtplib
import ssl
from timezone import is_dst

context = ssl.create_default_context()


connection = sqlite3.connect(config.DB_PATH)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()

# gets the opening range breakdown strategy id
cursor.execute("""
    SELECT id from strategy WHERE name = 'opening_range_breakdown'
""")

strategy_id = cursor.fetchone()['id']

# Gets the symbol and name of stocks from table stock
# joins table stock_strategy and stock based on their stock id where the strategy id of each stock is "opening_range_breakdown"
cursor.execute("""
    select symbol, name
    from stock
    join stock_strategy on stock_strategy.stock_id = stock.id
    where stock_strategy.strategy_id = ?
""", (strategy_id,))

stocks = cursor.fetchall()

symbols = [stock['symbol'] for stock in stocks]

current_date = date.today().isoformat()

# adjust for day light savings time when grabbing minute bars from the start of the day to the end of the day
if is_dst():
    start_minute_bar = f"{current_date} 09:30-05:00"
    end_minute_bar = f"{current_date} 09:45-05:00"
else:
    start_minute_bar = f"{current_date} 09:30-04:00"
    end_minute_bar = f"{current_date} 09:45-04:00"

# Grabs api key
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [
    order.symbol for order in orders if order.status != 'canceled']

messages = []


for symbol in symbols:

    minute_bars = api.get_barset(
        symbol, "1Min", 1000, start=current_date, end=current_date).df

    # Checks whether the minute_bars.index is in the first 15 minutes
    opening_range_mask = (minute_bars.index >= start_minute_bar) & (
        minute_bars.index < end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask] # grabs minute bars from the first 15 minutes

    opening_range_low = opening_range_bars[symbol, 'low'].min() # grabs the lowest priced minute bar in the first 15 min, giving the bottom of the opening range

    opening_range_high = opening_range_bars[symbol, 'high'].max() # grabs the highest priced minute bar in the first 15 min, giving the top of the opening range

    opening_range = opening_range_high - opening_range_low # opening range

    after_opening_range_mask = minute_bars.index >= end_minute_bar 
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask] # grabs minute bars after the first 15 minutes

    after_opening_range_breakdown = after_opening_range_bars[
        after_opening_range_bars[symbol, 'close'] < opening_range_low]

    # if there is a stock meets the strategy criteria that we do not already have a position in
    # place a short limit order of 100 shares
    # limit price: current stock price
    # take profit: current price - opening range
    # stop loss: current price + opening range
    if not after_opening_range_breakdown.empty:
        if symbol not in existing_order_symbols:
            limit_price = after_opening_range_breakdown.iloc[0][symbol, 'close']

            message = f"selling short for {symbol} at {limit_price}, closed below {opening_range_low} \n\n {after_opening_range_breakdown.iloc[0][symbol]}\n\n"

            messages.append(message)
            print(message)
            try:

                # Alpaca API submit order following strategy
                api.submit_order(
                    symbol=symbol,
                    side='sell',
                    type='limit',
                    qty='100',
                    time_in_force='day',
                    order_class='bracket',
                    limit_price=limit_price,
                    take_profit=dict(
                        limit_price=limit_price - opening_range,
                    ),
                    stop_loss=dict(
                        stop_price=limit_price + opening_range,
                    )
                )
            except Exception as e:
                print(f"could not submit order {e}")
        # skip message as we already have a position
        else:
            print(f"Already an order for {symbol}, skipping")

# Emails user a trade notification
with smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT, context=context) as server:
    server.login(config.EMAIL_ADDRESS, config.EMAILL_PASSWORD)

    email_message = f"Subject: Trade Notifications for {current_date}\n\n"
    email_message += "\n\n".join(messages)
    server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, email_message)

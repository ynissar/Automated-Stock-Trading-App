# Used to drop sqlite tables

import sqlite3
import config

connection = sqlite3.connect('app.db')

cursor = connection.cursor()

# Drops table containing information about stock prices for each stock id
cursor.execute("""drop table stock_price""")

# Drops table containing information about stocks
cursor.execute("""drop table stock""")

# Drops table containing information about stocks and which strategy was being used on it
cursor.execute("""drop table stock_strategy""")

# Drops table containing information about stock strategies being used
cursor.execute("""drop table strategy""")

# commits changes to sqlite
connection.commit()

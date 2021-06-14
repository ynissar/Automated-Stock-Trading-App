import sqlite3
import config

connection = sqlite3.connect('app.db')

cursor = connection.cursor()

cursor.execute("""drop table stock_price""")

cursor.execute("""drop table stock""")

connection.commit()

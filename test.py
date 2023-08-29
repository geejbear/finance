from cs50 import SQL

db = SQL("sqlite:///finance.db")
rows = db.execute("SELECT * FROM portfolio")
prices = [dict["price"] for dict in rows]
print(prices)
print(sum(prices))
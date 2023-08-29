from cs50 import SQL

db = SQL("sqlite:///finance.db")
rows = db.execute("SELECT * FROM portfolio")
for dict in rows:
    print(dict.values())
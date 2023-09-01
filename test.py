from cs50 import SQL
from helpers import lookup

db = SQL("sqlite:///finance.db")
existing_shares = db.execute("SELECT shares FROM portfolio WHERE symbol = ?", "TSLA")
print(existing_shares)
####current_num_of_shares = float(existing_shares[0]["shares"]) + 2.0
##print(current_num_of_shares)
data = lookup("googl")
print(data["price"])

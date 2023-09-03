from cs50 import SQL
from helpers import lookup
import datetime

db = SQL("sqlite:///finance.db")

today = datetime.datetime.now().replace(microsecond=0)
print(today)
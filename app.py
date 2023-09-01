import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    if not session["user_id"]:
        return redirect("/login")
    else:
        portfolio_rows = db.execute("SELECT symbol, name, shares, price, total FROM portfolio WHERE clientid = ?", session["user_id"])
        users_rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        elements = ["Symbol", "Name", "Shares", "Price", "Total"]
        if not portfolio_rows:
            return render_template("index.html", cash=float(users_rows[0]["cash"]), elements=elements)
        else:
            values = portfolio_rows

            bought_shares = [dict["total"] for dict in portfolio_rows]
            total = "{:.2f}".format(float(users_rows[0]["cash"]) + float(sum(bought_shares)))
            cash = "{:.2f}".format(float(float(total) - float(sum(bought_shares))))
        return render_template("index.html", elements=elements, values=values, cash=cash, total=total)
    


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    
    elif request.method == "POST":
        symbol_rows = lookup(request.form.get("symbol"))
        shares_to_buy = str(request.form.get("shares")) 
        if symbol_rows == None: 
            return apology("Symbol not found", 400)
        elif shares_to_buy == "":
            return apology("Cannot by zero shares", 400)

        current_user = db.execute("SELECT * FROM users")
        available_cash = float(current_user[0]["cash"]) 
        bought_shares = "{:.2f}".format(float(shares_to_buy) * (symbol_rows["price"]))
        portfolio = db.execute("SELECT * FROM portfolio WHERE clientid = ?", session["user_id"])

        #you may touch starting from this line (with caution)        
        if available_cash - float(bought_shares) < 0:
            return apology("Not enough cash", 400)
        # # # # # # #
        # --- this code served once it's purpose --#
        # elif current_user[0]["cash"] == 10000.00:
        #         db.execute('''UPDATE portfolio SET name = ?, symbol = ?, shares = ?, price = ?, total = ? WHERE clientid = ?''',
        #                     symbol_rows["name"], symbol_rows["symbol"], num_of_shares, symbol_rows["price"], 
        #                     total_shares, int(current_user[0]["id"])
        #         ) 
        # # # # # # #
        elif symbol_rows["symbol"] in [dict["symbol"] for dict in portfolio]:
            #TODO UPDATE ALLA SELL()!
            existing_shares = float(portfolio[0]["shares"])
            current_num_of_shares = existing_shares + float(request.form.get("shares"))
            bought_shares = "{:.2}".format(current_num_of_shares * float(symbol_rows["price"]))
            db.execute( '''UPDATE portfolio SET shares = ?, total = ? WHERE symbol = ?''',
                  current_num_of_shares, bought_shares, symbol_rows["symbol"]
            )
            
            remaining_cash = available_cash - float(bought_shares) 
            db.execute("UPDATE users SET cash = ?", remaining_cash)
            return redirect("/")
        else:
            db.execute(
                '''INSERT INTO portfolio (name, symbol, shares, price, total, clientid) VALUES(?, ?, ?, ?, ?, ?)''', 
                        symbol_rows["name"], symbol_rows["symbol"], int(request.form.get("shares")), symbol_rows["price"], 
                        bought_shares, int(current_user[0]["id"])
            )
            remaining_cash = available_cash - float(bought_shares) 
            db.execute("UPDATE users SET cash = ?", remaining_cash)
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else: 
        symbol = request.form.get("symbol")
        rows = lookup(symbol)
        if rows == None:
            return apology("Symbol not found", 400)

        return render_template("quoted.html", name=rows["name"], price=rows["price"], symbol=rows["symbol"])


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        usernameRows = db.execute("SELECT username FROM users")

        if not username or username in usernameRows:
            return apology("invalid username / username already exists", 403)

        elif not password or password != confirmation:
            return apology("Invalid password / passwords do not match", 403)
        
        else:
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
            rows = db.execute("SELECT * FROM users WHERE username = ?", username)
            session["user_id"] = rows[0]["id"]
            
            #add a row to the portfolio database with null values
            #db.execute("INSERT INTO portfolio (name, symbol, shares, price, total, clientid) VALUES(?, ?, ?, ?, ?, ?)", "", "", 0, 0.00, 0.00, rows[0]["id"])
            
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        data_rows = db.execute("SELECT symbol FROM portfolio")
        all_symbols = [dict["symbol"] for dict in data_rows]
        return render_template("sell.html", symbols=all_symbols)
    elif request.method == "POST":
        ## get symbols and shares
        price = db.execute("SELECT price FROM portfolio WHERE symbol = ?", request.form.get("symbol"))

        #updating database 
        bought_shares = db.execute("SELECT shares FROM portfolio WHERE symbol = ?", request.form.get("symbol"))
        currect_num_of_shares = float(bought_shares[0]["shares"]) - float(request.form.get("shares"))
        if currect_num_of_shares < 0:
            return apology("Too many shares", 400)
        elif currect_num_of_shares == 0:
            db.execute("DELETE FROM portfolio WHERE symbol = ?", request.form.get("symbol"))
        # upadate new total from shares
        bought_shares = "{:.2f}".format(currect_num_of_shares * float(price[0]["price"]))

        #updating cash
        available_cash = db.execute("SELECT cash FROM users WHERE id = ?", int(session["user_id"]))
        remainig_cash = "{:.2f}".format(float(available_cash[0]["cash"]) + (float(int(request.form.get("shares")) * float(price[0]["price"]))))

        
        db.execute("UPDATE portfolio SET shares = ?, total = ? WHERE symbol = ?", currect_num_of_shares, bought_shares, request.form.get("symbol"))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", remainig_cash,  int(session["user_id"]))
        # update client-side

        # if all sold, maybe a python function to set rows to NULL, rather than
        ## having no data?
        return redirect("/")

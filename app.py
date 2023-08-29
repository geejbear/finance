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
    if session["user_id"] == None:
        return redirect("/login")
    else:
        portfolio_rows = db.execute("SELECT symbol, name, shares, price, total FROM portfolio WHERE clientid = ?", session["user_id"])
        elements = portfolio_rows[0].keys()
        values = portfolio_rows

        users_rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        total_shares = [dict["total"] for dict in portfolio_rows]
        total = "{:.2f}".format(float(users_rows[0]["cash"]) + float(sum(total_shares)))
        cash = "{:.2f}".format(float(float(total) - float(sum(total_shares))))
        return render_template("index.html", elements=elements, values=values, cash=cash, total=total)
    ## return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    
    elif request.method == "POST":
        # don't touch this code
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        rows = lookup(symbol)
        current_user = db.execute("SELECT * FROM users")

        available_cash = float(current_user[0]["cash"]) 
        total_shares = "{:.2f}".format(float(shares) * rows["price"]) 

        #you may touch starting from this line (with caution)        
        if rows == None:
            return apology("Symbol not found", 400)
        elif available_cash - float(total_shares) < 0:
            return apology("Not enough cash", 400)
        else:
            remaining_cash = available_cash - float(total_shares) 
            db.execute("UPDATE users SET cash = ?", remaining_cash)

            if current_user[0]["cash"] == 10000.00:
                db.execute("UPDATE portfolio SET name = ?, symbol = ?, shares = ?, price = ?, total = ? WHERE clientid = ?",
                            rows["name"], rows["symbol"], shares, rows["price"], total_shares, int(current_user[0]["id"])) 
            else:
                db.execute(
                    '''INSERT INTO portfolio (name, symbol, shares, price, total, clientid) VALUES(?, ?, ?, ?, ?, ?)''', 
                            rows["name"], rows["symbol"], shares, rows["price"], 
                            total_shares, int(current_user[0]["id"])
                )
                ##update cash and total


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
            db.execute("INSERT INTO portfolio (name, symbol, shares, price, total, clientid) VALUES(?, ?, ?, ?, ?, ?)", "", "", 0, 0.00, 0.00, rows[0]["id"])
            
            return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")

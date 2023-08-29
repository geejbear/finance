from cs50 import SQL

database = SQL("sqlite:///finance.db")
database.execute('''CREATE TABLE portfolio( 
                        symbol TEXT, 
                        name TEXT, 
                        shares INTEGER, 
                        price REAL, 
                        total REAL, 
                        clientid INTEGER, 
                        FOREIGN KEY(clientid) REFERENCES users(id)
                    );''')



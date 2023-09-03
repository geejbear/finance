from cs50 import SQL

database = SQL("sqlite:///finance.db")
database.execute('''CREATE TABLE history( 
                        time TEXT,
                        symbol TEXT, 
                        shares INTEGER, 
                        trans REAL, 
                        activity_id INTEGER, 
                        FOREIGN KEY(activity_id) REFERENCES users(id)
                    );'''
                )



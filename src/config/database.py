import pymysql

def get_database_connection():
    """
    Creates and returns a connection to the MySQL database.
    
    There is sometimes an error showing up in the IDE on the pymysql import. I am not sure why, but the connection works fine so you can ignore that error.
    """
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='password123',
            database='forex_tracker'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None 
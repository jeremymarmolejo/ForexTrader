print("Starting test...")
from config.database import get_database_connection

def test_connection():
    print("Attempting to connect...")
    connection = get_database_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        db_version = cursor.fetchone()
        print(f"Database version: {db_version[0]}")
        
        cursor.close()
        connection.close()
        print("Connection closed successfully")
    else:
        print("Failed to establish connection")

if __name__ == "__main__":
    print("Running test_connection...")
    test_connection()

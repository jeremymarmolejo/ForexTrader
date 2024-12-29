from config.database import get_database_connection
import hashlib
import sys
import termios
import tty
class TradeManager:
    def __init__(self, user_id):
        self.user_id = user_id
    
    def add_trade(self):
        print("\n=== Add New Trade ===")
        pair = input("Enter currency pair (e.g., EUR/USD): ")
        entry = float(input("Enter entry price: "))
        size = float(input("Enter position size: "))
        trade_type = input("Enter trade type (SHORT/LONG): ").upper()
        
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO trades (user_id) VALUES (%s)", (self.user_id,))
            trade_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO open_trades (trade_id, c_pair, entry, size, trade_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (trade_id, pair, entry, size, trade_type))
            
            conn.commit()
            print("Trade added successfully!")
            self.update_live_report()  # Update live report after adding trade
            
        except Exception as e:
            print(f"Error adding trade: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def view_open_trades(self):
        print("\n=== Open Trades ===")
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT t.trade_id, o.c_pair, o.entry, o.size, o.trade_type
                FROM trades t
                JOIN open_trades o ON t.trade_id = o.trade_id
                WHERE t.user_id = %s
            """, (self.user_id,))
            
            trades = cursor.fetchall()
            if trades:
                print("\nID | Pair    | Entry  | Size   | Type")
                print("-" * 40)
                for trade in trades:
                    print(f"{trade[0]:<3}| {trade[1]:<8}| {trade[2]:<7}| {trade[3]:<7}| {trade[4]}")
            else:
                print("No open trades found.")
                
        except Exception as e:
            print(f"Error viewing trades: {e}")
        finally:
            if conn:
                conn.close()

    def view_closed_trades(self):
        print("\n=== Closed Trades ===")
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT t.trade_id, c.c_pair, c.entry, c.exit_price, 
                       c.size, c.trade_type, c.trade_date,
                       ROUND((c.exit_price - c.entry) * c.size, 2) as profit_loss
                FROM trades t
                JOIN closed_trades c ON t.trade_id = c.trade_id
                WHERE t.user_id = %s
                ORDER BY c.trade_date DESC
            """, (self.user_id,))
            
            trades = cursor.fetchall()
            if trades:
                print("\nID | Pair    | Entry  | Exit   | Size   | Type | Date       | P/L")
                print("-" * 75)
                for trade in trades:
                    print(f"{trade[0]:<3}| {trade[1]:<8}| {trade[2]:<7}| {trade[3]:<7}| "
                          f"{trade[4]:<7}| {trade[5]:<5}| {trade[6]} | {trade[7]}")
            else:
                print("No closed trades found.")
                
        except Exception as e:
            print(f"Error viewing trades: {e}")
        finally:
            if conn:
                conn.close()

    def close_trade(self):
        print("\n=== Close Trade ===")
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            # Show open trades
            cursor.execute("""
                SELECT t.trade_id, o.c_pair, o.entry, o.size, o.trade_type
                FROM trades t
                JOIN open_trades o ON t.trade_id = o.trade_id
                WHERE t.user_id = %s
            """, (self.user_id,))
            
            trades = cursor.fetchall()
            if not trades:
                print("No open trades to close.")
                return
                
            print("\nOpen Trades:")
            print("ID | Pair    | Entry  | Size   | Type")
            print("-" * 40)
            for trade in trades:
                print(f"{trade[0]:<3}| {trade[1]:<8}| {trade[2]:<7}| {trade[3]:<7}| {trade[4]}")
            
            # Get trade to close
            trade_id = int(input("\nEnter ID of trade to close: "))
            exit_price = float(input("Enter exit price: "))
            
            # Get the trade details
            cursor.execute("SELECT * FROM open_trades WHERE trade_id = %s", (trade_id,))
            trade = cursor.fetchone()
            
            if trade:
                # Insert into closed_trades
                cursor.execute("""
                    INSERT INTO closed_trades 
                    (trade_id, c_pair, entry, exit_price, size, trade_type, trade_date)
                    VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
                """, (trade[0], trade[1], trade[2], exit_price, trade[3], trade[4]))
                
                # Delete from open_trades
                cursor.execute("DELETE FROM open_trades WHERE trade_id = %s", (trade_id,))
                
                conn.commit()
                print("Trade closed successfully!")
                self.update_regular_report()  # Update regular report after closing trade
                self.update_live_report()     # Update live report since open positions changed
            else:
                print("Trade not found.")
                
        except Exception as e:
            print(f"Error closing trade: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def update_live_report(self):
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            # Get or create report_id for user
            cursor.execute("SELECT rep_id FROM Report WHERE user_id = %s", (self.user_id,))
            report = cursor.fetchone()
            
            if not report:
                cursor.execute("INSERT INTO Report (user_id) VALUES (%s)", (self.user_id,))
                report_id = cursor.lastrowid
            else:
                report_id = report[0]
            
            # Calculate open P/L
            cursor.execute("""
                SELECT COALESCE(SUM(size), 0)
                FROM open_trades o
                JOIN trades t ON o.trade_id = t.trade_id
                WHERE t.user_id = %s
            """, (self.user_id,))
            
            open_pl = cursor.fetchone()[0]
            
            # Update Live_Report
            cursor.execute("""
                INSERT INTO Live_Report (rep_id, open_pl)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE open_pl = %s
            """, (report_id, open_pl, open_pl))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error updating live report: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def update_regular_report(self):
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            # Get or create report_id for user
            cursor.execute("SELECT rep_id FROM Report WHERE user_id = %s", (self.user_id,))
            report = cursor.fetchone()
            
            if not report:
                cursor.execute("INSERT INTO Report (user_id) VALUES (%s)", (self.user_id,))
                report_id = cursor.lastrowid
            else:
                report_id = report[0]
            
            # Calculate metrics
            cursor.execute("""
                SELECT 
                    COALESCE(
                        COUNT(CASE WHEN (exit_price - entry) * size > 0 THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(*), 0), 0) as win_loss,
                    (
                        SELECT c_pair
                        FROM closed_trades c2
                        JOIN trades t2 ON c2.trade_id = t2.trade_id
                        WHERE t2.user_id = %s
                        GROUP BY c_pair
                        ORDER BY SUM((exit_price - entry) * size) DESC
                        LIMIT 1
                    ) as top_cpair,
                    1.5 as rr_ratio,  -- This is hardcoded for now
                    COALESCE(SUM((exit_price - entry) * size), 0) as net_pl
                FROM closed_trades c
                JOIN trades t ON c.trade_id = t.trade_id
                WHERE t.user_id = %s
            """, (self.user_id, self.user_id))
            
            metrics = cursor.fetchone()
            
            # Update Regular_Report
            cursor.execute("""
                INSERT INTO Regular_Report (rep_id, win_loss, top_cpair, rr_ratio, net_pl)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    win_loss = %s,
                    top_cpair = %s,
                    rr_ratio = %s,
                    net_pl = %s
            """, (report_id, metrics[0], metrics[1], metrics[2], metrics[3],
                  metrics[0], metrics[1], metrics[2], metrics[3]))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error updating regular report: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def view_reports(self):
        """
        Display the reports menu and handle report viewing options.
        Users can view Live Report (current open trades P/L) or
        Regular Report (historical performance metrics).
        """
        while True:
            print("\n=== Trading Reports ===")
            print("1. Live Report")
            print("2. Regular Report")
            print("3. Back to Main Menu")
            
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                # View Live Report
                open_pl = self.update_live_report()  # This will ask for current prices
                if open_pl is not None:
                    print("\n=== Live Report ===")
                    print(f"Open P/L: ${open_pl:.2f}")
                    input("\nPress Enter to continue...")
                    
            elif choice == "2":
                try:
                    conn = get_database_connection()
                    cursor = conn.cursor()
                    
                    # Get report_id
                    cursor.execute("SELECT rep_id FROM Report WHERE user_id = %s", (self.user_id,))
                    report = cursor.fetchone()
                    
                    if report:
                        report_id = report[0]
                        cursor.execute("""
                            SELECT win_loss, top_cpair, rr_ratio, net_pl
                            FROM Regular_Report
                            WHERE rep_id = %s
                        """, (report_id,))
                        
                        reg_report = cursor.fetchone()
                        if reg_report:
                            print("\n=== Regular Report ===")
                            print(f"Win Rate: {reg_report[0]:.1f}%")
                            if reg_report[1]:  # Only show if there's a top pair
                                print(f"Top Performing Pair: {reg_report[1]}")
                            print(f"Risk/Reward Ratio: {reg_report[2]:.2f}")
                            print(f"Net P/L: ${reg_report[3]:.2f}")
                        else:
                            print("No regular report data available.")
                    else:
                        print("No report data available.")
                    
                    input("\nPress Enter to continue...")
                        
                except Exception as e:
                    print(f"Error viewing regular report: {e}")
                finally:
                    if conn:
                        conn.close()
                    
            elif choice == "3":
                return
            else:
                print("Invalid choice!")

def login():
    print("\n=== Login ===")
    username = input("Username: ")
    password = input_password("Password: ")  # Use the custom function
    
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM users WHERE username = %s AND password_hash = %s", 
                      (username, hashed_password))
        user = cursor.fetchone()
        
        if user:
            print(f"Welcome back, {username}!")
            return user[0]
        else:
            print("Invalid username or password")
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def input_password(prompt="Password: "):
    """Custom password input masking with '*'."""
    print(prompt, end='', flush=True)
    password = ""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            char = sys.stdin.read(1)
            if char == '\r' or char == '\n':  # Enter key pressed
                print()  # Move to the next line
                break
            elif char == '\x7f':  # Backspace
                if len(password) > 0:
                    password = password[:-1]
                    sys.stdout.write("\b \b")  # Erase the last '*' in the console
                    sys.stdout.flush()
            else:
                password += char
                sys.stdout.write("*")  # Print an asterisk
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return password

def register():
    print("\n=== Register ===")
    username = input("Username: ")
    email = input("Email: ")
    password = input_password("Password: ")  # Use the custom function
    
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, (username, email, hashed_password))
        
        conn.commit()
        print("Registration successful! Please login.")
        
    except Exception as e:
        print(f"Registration error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def main():
    while True:
        print("\n=== Forex Trade Tracker ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            user_id = login()
            if user_id:
                trade_manager = TradeManager(user_id)
                trading_menu(trade_manager)
        elif choice == "2":
            register()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def trading_menu(manager):
    while True:
        print("\n=== Trading Menu ===")
        print("1. Add New Trade")
        print("2. View Open Trades")
        print("3. Close Trade")
        print("4. View Closed Trades")
        print("5. View Reports")
        print("6. Logout")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == "1":
            manager.add_trade()
        elif choice == "2":
            manager.view_open_trades()
        elif choice == "3":
            manager.close_trade()
        elif choice == "4":
            manager.view_closed_trades()
        elif choice == "5":
            manager.view_reports()
        elif choice == "6":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

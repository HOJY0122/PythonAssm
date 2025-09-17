import sqlite3
import os
import shutil
from datetime import datetime

def get_db_path():
    """Get the database file path"""
    return os.path.join(os.path.expanduser("~"), "pomodoro_data.db")

def check_database_exists():
    """Check if database file exists"""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print("ERROR: Database file not found!")
        print(f"Expected location: {db_path}")
        print("\nRun your main application first to create the database.")
        return False
    return True

def view_all_data():
    """View all data in the database"""
    if not check_database_exists():
        return
        
    db_path = get_db_path()
    print(f"Reading database from: {db_path}")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Show database info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        print("=" * 80)
        
        # Show users table
        print("\nUSERS TABLE:")
        print("-" * 70)
        cursor.execute("SELECT id, username, created_at, total_sessions, total_minutes FROM users")
        users = cursor.fetchall()
        
        if users:
            print(f"{'ID':<5} {'Username':<15} {'Created At':<20} {'Sessions':<10} {'Minutes':<10}")
            print("-" * 70)
            for user in users:
                created_date = user[2][:10] if user[2] else "Unknown"  # Show date only
                print(f"{user[0]:<5} {user[1]:<15} {created_date:<20} {user[3]:<10} {user[4]:<10}")
                
            print(f"\nTotal users: {len(users)}")
        else:
            print("No users found. Create an account in the main application first.")
        
        # Show pomodoro logs table  
        print("\nPOMODORO SESSIONS TABLE:")
        print("-" * 90)
        cursor.execute("""SELECT id, username, start_time, duration_minutes, session_type, completed 
                         FROM pomodoro_logs ORDER BY start_time DESC LIMIT 20""")
        logs = cursor.fetchall()
        
        if logs:
            print(f"{'ID':<5} {'User':<12} {'Date':<12} {'Time':<8} {'Duration':<8} {'Type':<12} {'Status':<8}")
            print("-" * 90)
            for log in logs:
                # Parse datetime
                try:
                    dt = datetime.fromisoformat(log[2].replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d')
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    date_str = "Unknown"
                    time_str = "Unknown"
                
                status = "DONE" if log[5] else "SKIP"
                print(f"{log[0]:<5} {log[1]:<12} {date_str:<12} {time_str:<8} {log[3]:<8} {log[4]:<12} {status:<8}")
                
            print(f"\nShowing last 20 sessions (total sessions in database)")
        else:
            print("No session logs found. Complete some Pomodoro sessions first.")
            
        # Show password security check
        print("\nPASSWORD SECURITY CHECK:")
        print("-" * 60)
        cursor.execute("SELECT username, password_hash, password_salt FROM users")
        security_data = cursor.fetchall()
        
        if security_data:
            print(f"{'Username':<15} {'Hash Preview':<15} {'Salt Preview':<12} {'Status':<10}")
            print("-" * 60)
            for user_data in security_data:
                username, hash_val, salt_val = user_data
                hash_preview = hash_val[:10] + "..." if hash_val else "NONE"
                salt_preview = salt_val[:8] + "..." if salt_val else "NONE"
                status = "SECURE" if hash_val and salt_val else "INSECURE"
                print(f"{username:<15} {hash_preview:<15} {salt_preview:<12} {status:<10}")
        
        print("\nNOTE: Passwords are securely hashed and cannot be viewed in plain text.")
        
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

def show_user_stats():
    """Show detailed stats for a specific user"""
    if not check_database_exists():
        return
        
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all usernames
        cursor.execute("SELECT username FROM users")
        users = [row[0] for row in cursor.fetchall()]
        
        if not users:
            print("No users in database.")
            return
            
        print("Available users:")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user}")
        
        try:
            choice = int(input("\nEnter user number: ")) - 1
            if 0 <= choice < len(users):
                username = users[choice]
                
                print(f"\nDETAILED STATS FOR: {username}")
                print("=" * 50)
                
                # Basic stats
                cursor.execute("SELECT total_sessions, total_minutes FROM users WHERE username = ?", (username,))
                basic = cursor.fetchone()
                if basic:
                    print(f"Total Sessions: {basic[0]}")
                    print(f"Total Minutes: {basic[1]}")
                    print(f"Total Hours: {basic[1]/60:.1f}")
                
                # Today's sessions
                cursor.execute("""SELECT COUNT(*) FROM pomodoro_logs 
                                 WHERE username = ? AND session_type = 'work' 
                                 AND DATE(start_time) = DATE('now') AND completed = 1""", (username,))
                today = cursor.fetchone()[0]
                print(f"Today's Sessions: {today}")
                
                # This week's sessions
                cursor.execute("""SELECT COUNT(*) FROM pomodoro_logs 
                                 WHERE username = ? AND session_type = 'work' 
                                 AND DATE(start_time) >= DATE('now', 'weekday 0', '-6 days') 
                                 AND completed = 1""", (username,))
                week = cursor.fetchone()[0]
                print(f"This Week's Sessions: {week}")
                
                # Recent sessions
                cursor.execute("""SELECT start_time, duration_minutes, session_type, completed 
                                 FROM pomodoro_logs WHERE username = ? 
                                 ORDER BY start_time DESC LIMIT 10""", (username,))
                recent = cursor.fetchall()
                
                print(f"\nRecent Sessions (last 10):")
                print("-" * 50)
                if recent:
                    print(f"{'Date':<12} {'Time':<8} {'Duration':<8} {'Type':<12} {'Status':<8}")
                    print("-" * 50)
                    for session in recent:
                        try:
                            dt = datetime.fromisoformat(session[0].replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d')
                            time_str = dt.strftime('%H:%M')
                        except:
                            date_str = "Unknown"
                            time_str = "Unknown"
                        
                        status = "DONE" if session[3] else "SKIP"
                        print(f"{date_str:<12} {time_str:<8} {session[1]:<8} {session[2]:<12} {status:<8}")
                else:
                    print("No sessions found for this user.")
                    
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def clear_database():
    """Clear all data from database (be careful!)"""
    if not check_database_exists():
        return
        
    print("WARNING: This will delete ALL data from the database!")
    print("This includes all users, passwords, and session history.")
    confirm = input("Type 'DELETE' (all caps) to confirm: ")
    
    if confirm == "DELETE":
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM pomodoro_logs")
            cursor.execute("DELETE FROM users")
            conn.commit()
            print("SUCCESS: All data has been deleted from the database.")
        except Exception as e:
            print(f"Error deleting data: {e}")
        finally:
            conn.close()
    else:
        print("Operation cancelled. No data was deleted.")

def export_data():
    """Export data to text file"""
    if not check_database_exists():
        return
        
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        export_file = "database_export.txt"
        with open(export_file, 'w') as f:
            f.write("TAR UMT Student Assistant - Database Export\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            # Export users
            f.write("USERS:\n")
            f.write("-" * 40 + "\n")
            cursor.execute("SELECT id, username, created_at, total_sessions, total_minutes FROM users")
            users = cursor.fetchall()
            
            for user in users:
                f.write(f"ID: {user[0]}\n")
                f.write(f"Username: {user[1]}\n")
                f.write(f"Created: {user[2]}\n")
                f.write(f"Total Sessions: {user[3]}\n")
                f.write(f"Total Minutes: {user[4]}\n")
                f.write("-" * 40 + "\n")
            
            # Export sessions
            f.write("\nSESSIONS:\n")
            f.write("-" * 40 + "\n")
            cursor.execute("SELECT * FROM pomodoro_logs ORDER BY start_time DESC")
            logs = cursor.fetchall()
            
            for log in logs:
                f.write(f"Session ID: {log[0]}\n")
                f.write(f"User: {log[1]}\n")
                f.write(f"Start Time: {log[2]}\n")
                f.write(f"Duration: {log[3]} minutes\n")
                f.write(f"Type: {log[4]}\n")
                f.write(f"Completed: {'Yes' if log[5] else 'No'}\n")
                f.write("-" * 40 + "\n")
        
        print(f"SUCCESS: Data exported to {export_file}")
        
    except Exception as e:
        print(f"Error exporting data: {e}")
    finally:
        conn.close()

def copy_to_desktop():
    """Copy database and export files to desktop"""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        
        if not os.path.exists(desktop):
            print("ERROR: Desktop folder not found!")
            return
            
        print("Copying files to desktop...")
        print("-" * 40)
        
        # Copy database file
        db_path = get_db_path()
        if os.path.exists(db_path):
            dest_db = os.path.join(desktop, "pomodoro_data.db")
            shutil.copy2(db_path, dest_db)
            print(f"SUCCESS: Database copied to {dest_db}")
        else:
            print("WARNING: Database file not found, nothing to copy")
        
        # Copy export file if it exists
        export_file = "database_export.txt"
        if os.path.exists(export_file):
            dest_export = os.path.join(desktop, export_file)
            shutil.copy2(export_file, dest_export)
            print(f"SUCCESS: Export file copied to {dest_export}")
        else:
            print("NOTE: No export file found. Use option 3 to create one first.")
            
        print("\nYou can now find your files on the Desktop!")
        
    except Exception as e:
        print(f"ERROR: Failed to copy files to desktop: {e}")

def main():
    """Main menu for database operations"""
    while True:
        print("\n" + "="*60)
        print("DATABASE VIEWER - TAR UMT Student Assistant")
        print("="*60)
        print(f"Database location: {get_db_path()}")
        print(f"Export location: {os.getcwd()}")
        print("="*60)
        print("1. View all data")
        print("2. View user statistics")  
        print("3. Export data to file")
        print("4. Clear database (WARNING: Deletes everything!)")
        print("5. Copy files to Desktop")
        print("6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                view_all_data()
            elif choice == "2":
                show_user_stats()
            elif choice == "3":
                export_data()
            elif choice == "4":
                clear_database()
            elif choice == "5":
                copy_to_desktop()
            elif choice == "6":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-6.")
                
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
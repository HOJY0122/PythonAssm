"""
Fixed Database Module - Secure SQLite Implementation
Following tutor's pattern with proper password hashing
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime


class PomodoroDatabase:
    """Secure database class using SQLite with proper password hashing"""

    def __init__(self):
        self.db_path = os.path.join(
            os.path.expanduser("~"), "pomodoro_data.db")
        self.connected = True
        self._create_tables_if_not_exist()
        print("Database connected successfully!")

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _create_tables_if_not_exist(self):
        """Create necessary database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Users table with secure password storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_sessions INTEGER DEFAULT 0,
                    total_minutes INTEGER DEFAULT 0
                )
            """)

            # Pomodoro logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pomodoro_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_minutes INTEGER NOT NULL,
                    session_type TEXT DEFAULT 'work',
                    completed BOOLEAN DEFAULT 1,
                    FOREIGN KEY (username) REFERENCES users (username)
                )
            """)

            conn.commit()

        except Exception as e:
            raise Exception(f"Failed to create database tables: {e}")
        finally:
            conn.close()

    def _hash_password(self, password):
        """Hash password with salt - following tutor's pattern"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt

    def _verify_password(self, stored_hash, stored_salt, password):
        """Verify password against stored hash and salt"""
        password_hash = hashlib.sha256(
            (password + stored_salt).encode()).hexdigest()
        return password_hash == stored_hash

    def register_user(self, username, password):
        """Register a new user with secure password hashing"""
        try:
            if not username or not password:
                return False, "Username and password are required"

            if len(username) < 3:
                return False, "Username must be at least 3 characters"

            if len(password) < 4:
                return False, "Password must be at least 4 characters"

            conn = self.get_connection()
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute(
                "SELECT username FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False, "Username already exists"

            # Hash password and create user
            password_hash, password_salt = self._hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, password_salt) VALUES (?, ?, ?)",
                (username, password_hash, password_salt)
            )

            conn.commit()
            conn.close()
            return True, "Account created successfully!"

        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def authenticate_user(self, username, password):
        """Authenticate user login using secure password verification"""
        try:
            if not username or not password:
                return False, "Username and password are required"

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, password_hash, password_salt FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                stored_username, stored_hash, stored_salt = result
                if self._verify_password(stored_hash, stored_salt, password):
                    return True, "Login successful!"
                else:
                    return False, "Invalid username or password"
            else:
                return False, "Invalid username or password"

        except Exception as e:
            return False, f"Login failed: {str(e)}"

    def save_session(self, username, duration_minutes, session_type='work', completed=True):
        """Save a completed study session"""
        try:
            if not username or duration_minutes <= 0:
                return False, "Invalid session data"

            conn = self.get_connection()
            cursor = conn.cursor()

            # Insert session log
            cursor.execute(
                "INSERT INTO pomodoro_logs (username, duration_minutes, session_type, completed) VALUES (?, ?, ?, ?)",
                (username, duration_minutes, session_type, completed)
            )

            # Update user statistics if it's a completed work session
            if completed and session_type == 'work':
                cursor.execute(
                    "UPDATE users SET total_sessions = total_sessions + 1, total_minutes = total_minutes + ? WHERE username = ?",
                    (duration_minutes, username)
                )

            conn.commit()
            conn.close()
            return True, "Session saved successfully"

        except Exception as e:
            return False, f"Failed to save session: {str(e)}"

    def get_user_stats(self, username):
        """Get comprehensive user statistics"""
        try:
            if not username:
                return None, "Username is required"

            conn = self.get_connection()
            cursor = conn.cursor()

            # Get basic user stats
            cursor.execute(
                "SELECT total_sessions, total_minutes FROM users WHERE username = ?",
                (username,)
            )
            user_result = cursor.fetchone()

            if not user_result:
                conn.close()
                return None, "User not found"

            total_sessions, total_minutes = user_result

            # Get today's sessions
            cursor.execute(
                """SELECT COUNT(*) FROM pomodoro_logs 
                   WHERE username = ? AND session_type = 'work' 
                   AND DATE(start_time) = DATE('now') AND completed = 1""",
                (username,)
            )
            today_sessions = cursor.fetchone()[0] or 0

            # Get this week's sessions and minutes
            cursor.execute(
                """SELECT COUNT(*), COALESCE(SUM(duration_minutes), 0) 
                   FROM pomodoro_logs 
                   WHERE username = ? AND session_type = 'work' 
                   AND DATE(start_time) >= DATE('now', 'weekday 0', '-6 days') 
                   AND completed = 1""",
                (username,)
            )
            week_result = cursor.fetchone()
            week_sessions, week_minutes = week_result if week_result else (
                0, 0)

            # Get average session duration
            cursor.execute(
                """SELECT AVG(duration_minutes) 
                   FROM pomodoro_logs 
                   WHERE username = ? AND session_type = 'work' AND completed = 1""",
                (username,)
            )
            avg_duration_result = cursor.fetchone()
            avg_duration = avg_duration_result[0] if avg_duration_result and avg_duration_result[0] else 0

            conn.close()

            result = {
                'total_sessions': total_sessions or 0,
                'total_minutes': total_minutes or 0,
                'today_sessions': today_sessions,
                'week_sessions': week_sessions or 0,
                'week_minutes': week_minutes or 0,
                'avg_duration': float(avg_duration)
            }

            return result, "Stats retrieved successfully"

        except Exception as e:
            return None, f"Failed to get statistics: {str(e)}"

    def get_session_history(self, username, limit=50):
        """Get user's session history"""
        try:
            if not username:
                return [], "Username is required"

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """SELECT start_time, duration_minutes, session_type, completed
                   FROM pomodoro_logs 
                   WHERE username = ? 
                   ORDER BY start_time DESC 
                   LIMIT ?""",
                (username, limit)
            )

            history = cursor.fetchall()
            conn.close()

            return history or [], "History retrieved successfully"

        except Exception as e:
            return [], f"Failed to get history: {str(e)}"

    def close(self):
        """Close database connection"""
        self.connected = False

    # Compatibility method for existing code
    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Execute database query with error handling - compatibility method"""
        if not self.connected:
            raise Exception("Database not connected")

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(query, params or ())

            if fetch_one:
                result = cursor.fetchone()
                conn.close()
                return result
            elif fetch_all:
                result = cursor.fetchall()
                conn.close()
                return result
            else:
                conn.commit()
                rowcount = cursor.rowcount
                conn.close()
                return rowcount

        except Exception as e:
            if 'conn' in locals():
                conn.close()
            raise Exception(f"Database operation failed: {e}")

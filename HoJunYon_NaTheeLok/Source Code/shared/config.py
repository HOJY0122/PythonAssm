"""
Fixed Shared Configuration Module
Uses SQLite instead of MySQL, following tutor's secure pattern
"""

import os

# ========================================
# DATABASE CONFIGURATION (SQLite)
# ========================================
# SQLite database path - stores in user's home directory
DB_PATH = os.path.join(os.path.expanduser("~"), "pomodoro_data.db")

# ========================================
# TIMER CONFIGURATION
# ========================================
TIMER_CONFIG = {
    'work_time': 25 * 60,           # 25 minutes in seconds
    'break_time': 5 * 60,           # 5 minutes in seconds
    'long_break_time': 15 * 60,     # 15 minutes in seconds
    'sessions_until_long_break': 4  # Number of sessions before long break
}

# ========================================
# LIGHT THEME COLORS
# ========================================
LIGHT_COLORS = {
    'primary': '#2E86AB',          # Ocean Blue
    'secondary': '#A23B72',        # Magenta
    'accent': '#F18F01',           # Orange
    'warning': '#C73E1D',          # Red Orange
    'info': '#6A994E',             # Green
    'dark': '#2D3748',             # Dark Gray
    'light': '#F7FAFC',            # Very Light Gray
    'success': '#38A169',          # Green
    'danger': '#E53E3E',           # Red
    'background': '#F0F4F8',       # Light Blue Gray
    'white': '#FFFFFF',
    'text': '#2D3748',
    'text_secondary': '#718096',
    'border': '#E2E8F0',
    'shadow': '#CBD5E0',
    'gradient_start': '#667eea',
    'gradient_end': '#764ba2'
}

# ========================================
# DARK THEME COLORS
# ========================================
DARK_COLORS = {
    'primary': '#4299E1',          # Light Blue
    'secondary': '#D53F8C',        # Pink
    'accent': '#F6AD55',           # Light Orange
    'warning': '#FC8181',          # Light Red
    'info': '#68D391',             # Light Green
    'dark': '#1A202C',             # Very Dark
    'light': '#2D3748',            # Dark Gray
    'success': '#48BB78',          # Green
    'danger': '#F56565',           # Light Red
    'background': '#1A202C',       # Dark Background
    'white': '#2D3748',            # Dark Card
    'text': '#F7FAFC',             # Light Text
    'text_secondary': '#A0AEC0',   # Gray Text
    'border': '#4A5568',
    'shadow': '#2D3748',
    'gradient_start': '#667eea',
    'gradient_end': '#764ba2'
}

# Current theme - starts with light mode
COLORS = LIGHT_COLORS.copy()

# ========================================
# FONT CONFIGURATION
# ========================================
FONTS = {
    'header': ("Segoe UI", 20, "bold"),
    'subheader': ("Segoe UI", 16, "bold"),
    'label': ("Segoe UI", 11),
    'timer': ("Segoe UI", 42, "bold"),
    'button': ("Segoe UI", 11, "bold"),
    'small': ("Segoe UI", 9),
    'tiny': ("Segoe UI", 8)
}

# ========================================
# APPLICATION STATE
# ========================================
APP_STATE = {
    'running': True,
    'database': None,
    'dark_mode': False
}

# ========================================
# STUDY TIPS AND MOTIVATIONAL MESSAGES
# ========================================
STUDY_TIPS = [
    "Focus is the key to success!",
    "Every session counts towards your goals",
    "You're building great study habits",
    "Consistency beats perfection",
    "Keep up the excellent work!",
    "Success is built one session at a time",
    "Knowledge grows with every focus session",
    "Celebrate your progress today!",
    "Energy flows where attention goes",
    "Champions are made through daily practice"
]

MOTIVATIONAL_MESSAGES = [
    "Amazing work! You're on fire today!",
    "You're becoming more focused every session!",
    "Great job! Keep this momentum going!",
    "Fantastic effort! You're a study superstar!",
    "Outstanding! You're reaching new heights!",
    "Perfect focus! You're in the zone!",
    "Brilliant work! Quality over quantity!",
    "Excellent! Your dedication is inspiring!"
]

# Global reminders list for Simple Reminder App (unchanged)
reminders = []

# ========================================
# THEME MANAGEMENT FUNCTIONS
# ========================================


def toggle_theme():
    """Toggle between light and dark theme"""
    global COLORS
    APP_STATE['dark_mode'] = not APP_STATE['dark_mode']
    COLORS.update(DARK_COLORS if APP_STATE['dark_mode'] else LIGHT_COLORS)
    return APP_STATE['dark_mode']


def apply_theme_to_window(window):
    """Apply current theme to a tkinter window"""
    window.configure(bg=COLORS['background'])

# ========================================
# UTILITY FUNCTIONS
# ========================================


def safe_int(value, default=0):
    """Safely convert value to integer with default fallback"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def format_time(seconds):
    """Format seconds into MM:SS format"""
    try:
        minutes = max(0, seconds) // 60
        secs = max(0, seconds) % 60
        return f"{minutes:02d}:{secs:02d}"
    except:
        return "00:00"


def center_window(window, width, height):
    """Center a window on the screen"""
    try:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(relief='raised', bd=1)
    except:
        window.geometry(f"{width}x{height}")


def cleanup_application():
    """Cleanup application resources on exit"""
    APP_STATE['running'] = False
    if APP_STATE['database']:
        try:
            APP_STATE['database'].close()
        except:
            pass

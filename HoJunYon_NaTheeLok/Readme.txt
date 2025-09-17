TAR UMT Student Assistant Software

Authors: HO JUN YON and NA THEE LOK  
Course: AMCS1034 Software Development Fundamentals  
Assignment: Student Assistant App with Pomodoro Timer and Reminder System

Description

A comprehensive student productivity suite featuring:
- Pomodoro Timer: Study sessions with breaks, progress tracking, and database integration
- Smart Reminders: Time-based notifications with categories and search functionality  
- User Authentication: Secure login system with individual user accounts
- Modern UI: Light/Dark themes with beautiful, responsive design

IMPORTANT SECURITY UPDATE

This version uses **secure password hashing** following the tutor's recommended pattern:
- Passwords are hashed with SHA-256 and random salt
- No plain text passwords are stored
- Uses SQLite database for easy deployment

System Requirements

Required (included with Python):
- Python 3.7 or higher
- tkinter (GUI library)
- sqlite3 (database)
- hashlib and secrets (security modules)

Optional:
- pygame (for enhanced sound notifications)

Quick Start

1. Download all files and place them in the same directory:
   '''
   Student_Assistant/
   ├── main.py
   ├── pomodoro_app.py
   ├── reminder_app.py
   ├── shared/
   │   ├── __init__.py
   │   ├── config.py
   │   ├── database.py
   │   └── ui_components.py
   '''

2. Run the application:
   python main.py
   

3. First time setup:
   - Click "Create New Account" on login screen
   - Choose username (minimum 3 characters)
   - Create password (minimum 4 characters)
   - Login with your new credentials

File Structure
'''
Source Code/
├── main.py                     # Main application entry point
├── pomodoro_app.py             # Pomodoro Timer application  
├── reminder_app.py             # Simple Reminder application
└── shared/
    ├── __init__.py             # Module initialization
    ├── config.py               # Application configuration and settings
    ├── database.py             # Secure database operations with SQLite
    └── ui_components.py        # Custom UI components
'''

## Features

Authentication & Security
- Secure password hashing with SHA-256 and salt
- User registration and login system
- Password-protected accounts
- User-specific data isolation

Pomodoro Timer
- 25-minute focus sessions with 5-minute breaks
- Long breaks (15 minutes) after every 4 sessions
- Progress tracking and statistics
- Session history with database storage
- Customizable timer settings
- Sound notifications
- Motivational messages

Reminder System  
- Time-based reminder notifications
- Category organization
- Search and filter functionality
- Mark as done/delete operations
- Real-time clock display
- User-specific reminders
- Sound alerts

User Interface
- Modern, professional design
- Light and Dark theme support
- Responsive layout
- Beautiful animations and transitions
- Error handling and user feedback

Database Information

The application uses SQLite database stored in your home directory:
- Database file: `~/pomodoro_data.db` 
- Automatic table creation
- No external database setup required
- Secure password storage with salting

## Troubleshooting

### Common Issues

"ModuleNotFoundError: No module named 'shared'"
- Make sure you're running from the correct directory
- Check that all files are in the correct structure
- Ensure `shared/__init__.py` exists

"Database connection failed"
- Check file permissions in your home directory
- Try running as administrator (Windows) or with appropriate permissions

Timer not starting or stopping unexpectedly
- Check for any error messages in the console
- Try restarting the application

Optional Sound Enhancement

For better sound notifications, install pygame:
'''bash
pip install pygame
'''

Usage Instructions

Using the Pomodoro Timer
1. Select "Launch Pomodoro Timer" from main menu
2. View your dashboard with study statistics  
3. Click "Start Focus Session" to begin a 25-minute work session
4. Use timer controls: Start, Pause, Reset, or Skip sessions
5. Take breaks: App automatically switches to 5-minute breaks
6. View history: Check your session history and progress
7. Customize settings: Adjust timer durations in Settings

Using the Reminder App
1. Select "Launch Reminder App" from main menu
2. Add reminders:
   - Enter your reminder message
   - Set date in YYYY-MM-DD format  
   - Set time in HH:MM:SS format
   - Optional: Add a category
3. Manage reminders: Mark as done, delete, or clear all
4. Search reminders: Use search function to find specific reminders
5. Get notifications: Reminders will alert you at specified time

---

Thank you for using TAR UMT Student Assistant Software!

Developed with heart for student productivity and academic success
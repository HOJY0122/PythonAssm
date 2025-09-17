"""
Pomodoro Timer Application - COMPLETE FIXED VERSION
Fixed database display issues and added comprehensive debugging

Authors: HO JUN YON AND NA THEE LOK
Course: AMCS1034 Software Development Fundamentals
"""

import random
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

# Import shared modules
from shared.config import *
from shared.database import PomodoroDatabase
from shared.ui_components import (AnimatedProgressBar, EnhancedButton,
                                  StatusCard)

# Try pygame for sound (optional)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Try winsound for Windows (optional)
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


class EnhancedPomodoroTimer:
    """Enhanced Pomodoro Timer with database integration"""

    def __init__(self, database, username):
        self.db = database
        self.username = username

        self.work_time = TIMER_CONFIG['work_time']
        self.break_time = TIMER_CONFIG['break_time']
        self.long_break_time = TIMER_CONFIG['long_break_time']

        self.current_time = self.work_time
        self.is_work_session = True
        self.session_count = 0
        self.timer_running = False
        self.paused = False
        self.timer_thread = None
        self.thread_stop_event = threading.Event()

        self.sound_enabled = True
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except:
                self.sound_enabled = False

        self.on_time_update = None
        self.on_session_complete = None
        self.on_state_change = None

    def set_callbacks(self, time_update=None, session_complete=None, state_change=None):
        """Set callback functions for timer events"""
        self.on_time_update = time_update
        self.on_session_complete = session_complete
        self.on_state_change = state_change

    def start_timer(self):
        """Start the timer"""
        try:
            if self.timer_running:
                return False

            self.timer_running = True
            self.paused = False
            self.thread_stop_event.clear()

            self._safe_callback(self.on_state_change, "started")

            self.timer_thread = threading.Thread(
                target=self._timer_loop, daemon=True)
            self.timer_thread.start()
            return True

        except Exception as e:
            print(f"ERROR starting timer: {e}")
            self.timer_running = False
            return False

    def pause_timer(self):
        """Pause/resume the timer"""
        try:
            if not self.timer_running:
                return False

            self.paused = not self.paused
            state = "paused" if self.paused else "resumed"
            self._safe_callback(self.on_state_change, state)
            return True
        except Exception as e:
            print(f"ERROR pausing timer: {e}")
            return False

    def stop_timer(self):
        """Stop the timer"""
        try:
            if not self.timer_running:
                return False

            self.timer_running = False
            self.paused = False
            self.thread_stop_event.set()

            if self.timer_thread and self.timer_thread.is_alive():
                self.timer_thread.join(timeout=2.0)

            self._safe_callback(self.on_state_change, "stopped")
            return True
        except Exception as e:
            print(f"ERROR stopping timer: {e}")
            return False

    def reset_timer(self):
        """Reset the timer to initial state"""
        try:
            was_running = self.timer_running
            if was_running:
                self.stop_timer()

            if self.is_work_session:
                self.current_time = self.work_time
            elif self.session_count % TIMER_CONFIG['sessions_until_long_break'] == 0:
                self.current_time = self.long_break_time
            else:
                self.current_time = self.break_time

            self._safe_callback(self.on_time_update, self.current_time)
            return True
        except Exception as e:
            print(f"ERROR resetting timer: {e}")
            return False

    def skip_session(self):
        """Skip current session and properly advance to next session type"""
        try:
            self.stop_timer()

            if self.is_work_session:
                # Save skipped work session as incomplete
                duration = self.work_time // 60
                print(
                    f"DEBUG: Saving skipped session - User: '{self.username}', Duration: {duration}")

                success, message = self.db.save_session(
                    self.username, duration, 'work', completed=False)

                print(
                    f"DEBUG: Skip session result - Success: {success}, Message: '{message}'")

                if not success:
                    print(f"ERROR: Failed to save skipped session: {message}")
                    messagebox.showwarning("Database Warning",
                                           f"Session skipped but couldn't save to database:\n{message}")

                # Increment session count even when skipping
                self.session_count += 1

                # Switch to appropriate break
                self._switch_to_break()
                messagebox.showinfo("Session Skipped",
                                    f"Work session {self.session_count} skipped.\nTime for a break!")
            else:
                # If skipping break, switch to work
                self._switch_to_work()
                messagebox.showinfo("Break Skipped",
                                    "Break skipped.\nReady for next work session!")

            # Notify completion callbacks to update UI
            self._safe_callback(self.on_session_complete, False)
            return True
        except Exception as e:
            print(f"ERROR in skip_session: {e}")
            return False

    def _timer_loop(self):
        """Main timer loop running in separate thread"""
        try:
            while self.timer_running and self.current_time > 0 and not self.thread_stop_event.is_set():
                if not self.paused:
                    time.sleep(1)
                    self.current_time -= 1
                    self._safe_callback(self.on_time_update, self.current_time)
                else:
                    time.sleep(0.1)

            if self.timer_running and self.current_time <= 0:
                self._complete_session(completed=True)
        except Exception as e:
            print(f"ERROR in timer loop: {e}")
            self.timer_running = False
            self._safe_callback(self.on_state_change, "error")

    def _complete_session(self, completed=True):
        """Handle session completion"""
        try:
            self.stop_timer()

            if completed:
                self._play_notification()

            if self.is_work_session and completed:
                self.session_count += 1
                duration = self.work_time // 60

                print(
                    f"DEBUG: Saving completed session - User: '{self.username}', Duration: {duration}")

                success, message = self.db.save_session(
                    self.username, duration, 'work', completed)

                print(
                    f"DEBUG: Complete session result - Success: {success}, Message: '{message}'")

                if not success:
                    print(
                        f"ERROR: Failed to save completed session: {message}")
                    messagebox.showwarning("Database Warning",
                                           f"Session completed but couldn't save to database:\n{message}")

                if completed:
                    motivation_msg = random.choice(MOTIVATIONAL_MESSAGES)
                    try:
                        messagebox.showinfo("Session Complete!",
                                            f"{motivation_msg}\n\n"
                                            f"You completed a {duration}-minute focus session!\n"
                                            f"Time for a well-deserved break!")
                    except Exception as e:
                        print(f"ERROR showing completion dialog: {e}")

                self._switch_to_break()

            elif not self.is_work_session and completed:
                try:
                    messagebox.showinfo("Break Complete!",
                                        "Break time is over!\n"
                                        "Ready for another productive session?")
                except Exception as e:
                    print(f"ERROR showing break completion dialog: {e}")

                self._switch_to_work()

            self._safe_callback(self.on_session_complete, completed)
        except Exception as e:
            print(f"ERROR in _complete_session: {e}")

    def _switch_to_break(self):
        """Switch to break mode"""
        try:
            self.is_work_session = False

            if self.session_count % TIMER_CONFIG['sessions_until_long_break'] == 0:
                self.current_time = self.long_break_time
            else:
                self.current_time = self.break_time
        except Exception as e:
            print(f"ERROR switching to break: {e}")
            self.current_time = self.break_time

    def _switch_to_work(self):
        """Switch to work mode"""
        try:
            self.is_work_session = True
            self.current_time = self.work_time
        except Exception as e:
            print(f"ERROR switching to work: {e}")
            self.current_time = self.work_time

    def _play_notification(self):
        """Play notification sound"""
        try:
            if self.sound_enabled:
                print("\a")  # System beep
        except Exception as e:
            print(f"ERROR playing notification: {e}")

    def _safe_callback(self, callback, *args):
        """Safely execute callback with error handling"""
        if callback:
            try:
                callback(*args)
            except Exception as e:
                print(f"ERROR in callback: {e}")

    def get_formatted_time(self):
        """Get formatted time string"""
        return format_time(self.current_time)

    def get_progress_percentage(self):
        """Get progress as percentage"""
        try:
            if self.is_work_session:
                total = self.work_time
            elif self.session_count % TIMER_CONFIG['sessions_until_long_break'] == 0:
                total = self.long_break_time
            else:
                total = self.break_time

            if total <= 0:
                return 0

            elapsed = total - self.current_time
            return max(0, min(100, (elapsed / total) * 100))
        except Exception as e:
            print(f"ERROR calculating progress: {e}")
            return 0

    def get_session_info(self):
        """Get current session information"""
        try:
            if self.is_work_session:
                return {
                    'type': 'work',
                    'title': 'Focus Time',
                    'color': COLORS['accent']
                }
            else:
                is_long_break = self.session_count % TIMER_CONFIG['sessions_until_long_break'] == 0
                return {
                    'type': 'break',
                    'title': 'Long Break' if is_long_break else 'Short Break',
                    'color': COLORS['success']
                }
        except Exception as e:
            print(f"ERROR getting session info: {e}")
            return {
                'type': 'work',
                'title': 'Focus Time',
                'color': COLORS['accent']
            }


class PomodoroApp:
    """Main Pomodoro Timer Application"""

    def __init__(self, current_user=None, return_callback=None):
        self.return_callback = return_callback
        self.current_user = current_user
        self.db = None
        self.timer = None
        self.current_window = None

        print(f"Starting Pomodoro Timer for user: {current_user}")
        self._init_application()

    def center_window_perfectly(self, window, width, height):
        """Center window EXACTLY in the middle of the screen"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        y = max(0, y - 20)  # Account for taskbar

        window.geometry(f"{width}x{height}+{x}+{y}")
        window.configure(relief='flat', bd=0)
        window.update_idletasks()
        window.lift()
        window.focus_force()

    def get_optimal_window_size(self, min_width=800, min_height=600):
        """Get optimal window size for pomodoro app"""
        if self.current_window:
            screen_width = self.current_window.winfo_screenwidth()
            screen_height = self.current_window.winfo_screenheight()
        else:
            screen_width = 1920  # Default assumption
            screen_height = 1080

        # Use smaller percentages for more reasonable window sizes
        if screen_width >= 1920:
            width_percent = 0.55   # 55% of screen width
            height_percent = 0.7   # 70% of screen height
        else:
            width_percent = 0.7    # 70% for smaller screens
            height_percent = 0.8   # 80% for smaller screens

        optimal_width = max(min_width, int(screen_width * width_percent))
        optimal_height = max(min_height, int(screen_height * height_percent))

        return optimal_width, optimal_height

    def _init_application(self):
        """Initialize the application"""
        try:
            print("DEBUG: Initializing database...")
            self.db = PomodoroDatabase()
            APP_STATE['database'] = self.db
            print("DEBUG: Database initialized successfully")

            if self.current_user:
                print(
                    f"DEBUG: Starting Pomodoro menu for user: {self.current_user}")
                self.show_pomodoro_menu()
            else:
                messagebox.showerror(
                    "Error", "No user provided for Pomodoro Timer")
                self.back_to_main_menu()
        except Exception as e:
            print(f"ERROR initializing application: {e}")
            messagebox.showerror("Application Error",
                                 f"Failed to initialize: {str(e)}")
            self.back_to_main_menu()

    def debug_database_for_user(self, operation="general"):
        """Debug database issues for current user"""
        try:
            print(
                f"\nDEBUG: Database check for user '{self.current_user}' - Operation: {operation}")

            # Check database connection
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Check all users in database
            cursor.execute("SELECT DISTINCT username FROM pomodoro_logs")
            all_users = cursor.fetchall()
            print(
                f"DEBUG: All users in database: {[user[0] for user in all_users]}")

            # Check exact match for current user
            cursor.execute(
                "SELECT COUNT(*) FROM pomodoro_logs WHERE username = ?", (self.current_user,))
            exact_count = cursor.fetchone()[0]
            print(
                f"DEBUG: Exact match sessions for '{self.current_user}': {exact_count}")

            # Check case-insensitive match
            cursor.execute(
                "SELECT COUNT(*) FROM pomodoro_logs WHERE LOWER(username) = LOWER(?)", (self.current_user,))
            case_insensitive_count = cursor.fetchone()[0]
            print(
                f"DEBUG: Case-insensitive match for '{self.current_user}': {case_insensitive_count}")

            # Show actual sessions for debugging
            cursor.execute("SELECT username, start_time, duration_minutes, session_type, completed FROM pomodoro_logs WHERE LOWER(username) = LOWER(?) ORDER BY start_time DESC LIMIT 5", (self.current_user,))
            sessions = cursor.fetchall()

            if sessions:
                print(f"DEBUG: Recent sessions found:")
                for session in sessions:
                    username, start_time, duration, session_type, completed = session
                    print(
                        f"  Username: '{username}' | {start_time} | {duration}min | {session_type} | {'COMPLETED' if completed else 'SKIPPED'}")
            else:
                print(
                    f"DEBUG: NO sessions found for user '{self.current_user}'")

            conn.close()

        except Exception as e:
            print(f"ERROR in database debug: {e}")

    def show_pomodoro_menu(self):
        """Show the main Pomodoro dashboard with better window sizing"""
        try:
            self.timer = EnhancedPomodoroTimer(self.db, self.current_user)

            self.current_window = tk.Tk()
            self.current_window.title(f"Pomodoro Timer - {self.current_user}")
            apply_theme_to_window(self.current_window)

            # Better window sizing and centering
            self.current_window.resizable(True, True)
            self.current_window.minsize(800, 600)

            # Get optimal size and center perfectly
            window_width, window_height = self.get_optimal_window_size(
                800, 600)
            self.center_window_perfectly(
                self.current_window, window_width, window_height)

            main_frame = tk.Frame(self.current_window, bg=COLORS['background'],
                                  padx=30, pady=25)
            main_frame.pack(expand=True, fill='both')

            # Enhanced Welcome Header with centered name
            header_frame = tk.Frame(main_frame, bg=COLORS['background'])
            header_frame.pack(fill='x', pady=(0, 25))

            # Back button (top right only)
            back_frame = tk.Frame(header_frame, bg=COLORS['background'])
            back_frame.pack(fill='x', pady=(0, 15))

            EnhancedButton(back_frame, text="Back to Main Menu",
                           command=self.back_to_main_menu, button_type='dark',
                           width=18, height=1).pack(side='right')

            # Centered welcome message
            welcome_label = tk.Label(header_frame, text=f"Welcome back, {self.current_user}!",
                                     font=("Segoe UI", 20, "bold"), fg=COLORS['primary'],
                                     bg=COLORS['background'])
            welcome_label.pack(anchor='center')

            # Enhanced Statistics Dashboard
            stats_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                   bd=2, padx=25, pady=20)
            stats_frame.pack(fill='x', pady=15)

            tk.Label(stats_frame, text="Your Progress Dashboard",
                     font=("Segoe UI", 14, "bold"),
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, 12))

            # Get and display enhanced statistics
            self.debug_database_for_user("stats")
            stats, stats_message = self.db.get_user_stats(self.current_user)
            print(f"DEBUG: Stats result - {stats}, Message: '{stats_message}'")

            if stats:
                # Create stats cards
                cards_frame = tk.Frame(stats_frame, bg=COLORS['white'])
                cards_frame.pack(fill='x', pady=8)

                # Today's sessions
                today_card = StatusCard(cards_frame, "Today's Sessions",
                                        stats['today_sessions'], "", COLORS['success'])
                today_card.grid(row=0, column=0, padx=8, pady=4, sticky='ew')

                # Weekly progress
                week_card = StatusCard(cards_frame, "This Week",
                                       f"{stats['week_sessions']} sessions", "", COLORS['info'])
                week_card.grid(row=0, column=1, padx=8, pady=4, sticky='ew')

                # Total time
                total_hours = stats['total_minutes'] // 60
                total_mins = stats['total_minutes'] % 60
                time_card = StatusCard(cards_frame, "Total Study Time",
                                       f"{total_hours}h {total_mins}m", "", COLORS['warning'])
                time_card.grid(row=1, column=0, padx=8, pady=4, sticky='ew')

                # Average session
                avg_card = StatusCard(cards_frame, "Average Session",
                                      f"{stats['avg_duration']:.1f} min", "", COLORS['primary'])
                avg_card.grid(row=1, column=1, padx=8, pady=4, sticky='ew')

                # Configure grid
                cards_frame.grid_columnconfigure(0, weight=1)
                cards_frame.grid_columnconfigure(1, weight=1)

            else:
                tk.Label(stats_frame, text="Ready to start your first session?\n"
                                           "Your progress will appear here!",
                         font=FONTS['label'], bg=COLORS['white'], fg=COLORS['text'],
                         justify='center').pack(pady=12)

            # Enhanced Action Buttons
            button_frame = tk.Frame(main_frame, bg=COLORS['background'])
            button_frame.pack(pady=20)

            # Main action button
            EnhancedButton(button_frame, text="Start Focus Session",
                           command=self.show_timer_window, button_type='danger',
                           width=32, height=2).pack(pady=10)

            # Secondary buttons grid
            secondary_frame = tk.Frame(button_frame, bg=COLORS['background'])
            secondary_frame.pack(pady=12)

            EnhancedButton(secondary_frame, text="Session History",
                           command=self.show_history_window, button_type='info',
                           width=16, height=2).pack(side=tk.LEFT, padx=6)

            EnhancedButton(secondary_frame, text="Settings",
                           command=self.show_settings_window, button_type='warning',
                           width=16, height=2).pack(side=tk.LEFT, padx=6)

            # Enhanced Motivational Section
            tip_frame = tk.Frame(main_frame, bg=COLORS['info'], relief='raised',
                                 bd=2, padx=20, pady=15)
            tip_frame.pack(fill='x', pady=15)

            tk.Label(tip_frame, text="Daily Motivation",
                     font=("Segoe UI", 12, "bold"),
                     bg=COLORS['info'], fg=COLORS['white']).pack()

            tip_text = random.choice(STUDY_TIPS)
            tk.Label(tip_frame, text=tip_text, font=FONTS['label'],
                     bg=COLORS['info'], fg=COLORS['white'],
                     wraplength=500, justify='center').pack(pady=6)

            self.current_window.protocol(
                "WM_DELETE_WINDOW", self.back_to_main_menu)
            self.current_window.mainloop()

        except Exception as e:
            print(f"ERROR in show_pomodoro_menu: {e}")
            messagebox.showerror(
                "Error", f"Failed to load main menu: {str(e)}")

    def show_timer_window(self):
        """Show the timer interface with better sizing"""
        try:
            timer_window = tk.Toplevel(self.current_window)
            timer_window.title("Focus Session Active")
            timer_window.configure(bg=COLORS['background'])
            timer_window.grab_set()

            # Better timer window sizing
            timer_window.resizable(True, True)
            timer_window.minsize(600, 500)

            # Get screen size for better sizing
            screen_width = timer_window.winfo_screenwidth()
            screen_height = timer_window.winfo_screenheight()

            # Use smaller, more reasonable size
            window_width = min(700, int(screen_width * 0.45))
            window_height = min(600, int(screen_height * 0.6))
            self.center_window_perfectly(
                timer_window, window_width, window_height)

            main_frame = tk.Frame(timer_window, bg=COLORS['background'],
                                  padx=25, pady=20)
            main_frame.pack(expand=True, fill='both')

            # Enhanced Session Info Header
            session_info = self.timer.get_session_info()
            header_frame = tk.Frame(main_frame, bg=COLORS['background'])
            header_frame.pack(fill='x', pady=(0, 15))

            self.session_label = tk.Label(header_frame, text=session_info['title'],
                                          font=("Segoe UI", 18, "bold"),
                                          fg=session_info['color'],
                                          bg=COLORS['background'])
            self.session_label.pack()

            # Enhanced Timer Display
            timer_frame = tk.Frame(main_frame, bg=session_info['color'],
                                   relief='raised', bd=3, padx=30, pady=25)
            timer_frame.pack(pady=15)

            self.time_label = tk.Label(timer_frame, text=self.timer.get_formatted_time(),
                                       font=("Segoe UI", 40, "bold"), fg=COLORS['white'],
                                       bg=session_info['color'])
            self.time_label.pack()

            # Enhanced Progress Section
            progress_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                      bd=2, padx=20, pady=15)
            progress_frame.pack(fill='x', pady=12)

            tk.Label(progress_frame, text="Session Progress", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, 8))

            self.progress_bar = AnimatedProgressBar(
                progress_frame, width=350, height=25)
            self.progress_bar.pack(pady=8)

            # Enhanced Control Panel
            control_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                     bd=2, padx=20, pady=15)
            control_frame.pack(pady=12)

            tk.Label(control_frame, text="Timer Controls", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, 12))

            # Control buttons grid
            button_grid = tk.Frame(control_frame, bg=COLORS['white'])
            button_grid.pack()

            self.start_btn = EnhancedButton(button_grid, text="Start",
                                            command=self.timer.start_timer, button_type='success',
                                            width=11, height=2)
            self.start_btn.grid(row=0, column=0, padx=6, pady=4)

            self.pause_btn = EnhancedButton(button_grid, text="Pause",
                                            command=self.timer.pause_timer, button_type='warning',
                                            width=11, height=2)
            self.pause_btn.grid(row=0, column=1, padx=6, pady=4)

            self.reset_btn = EnhancedButton(button_grid, text="Reset",
                                            command=self.timer.reset_timer, button_type='info',
                                            width=11, height=2)
            self.reset_btn.grid(row=1, column=0, padx=6, pady=4)

            self.skip_btn = EnhancedButton(button_grid, text="Skip",
                                           command=self.timer.skip_session, button_type='dark',
                                           width=11, height=2)
            self.skip_btn.grid(row=1, column=1, padx=6, pady=4)

            # Enhanced Session Stats
            stats_frame = tk.Frame(main_frame, bg=COLORS['light'], relief='raised',
                                   bd=1, padx=15, pady=10)
            stats_frame.pack(fill='x', pady=8)

            self.stats_label = tk.Label(stats_frame,
                                        text=f"Sessions Completed Today: {self.timer.session_count}",
                                        font=FONTS['label'], bg=COLORS['light'],
                                        fg=COLORS['text'])
            self.stats_label.pack()

            # Navigation
            EnhancedButton(main_frame, text="Back to Dashboard",
                           command=lambda: self._close_timer_window(
                               timer_window),
                           button_type='dark', width=18, height=2).pack(pady=12)

            # Set enhanced timer callbacks
            self.timer.set_callbacks(
                time_update=self.update_timer_display,
                session_complete=self.on_session_complete,
                state_change=self.on_timer_state_change
            )

            timer_window.protocol("WM_DELETE_WINDOW",
                                  lambda: self._close_timer_window(timer_window))

        except Exception as e:
            print(f"ERROR in show_timer_window: {e}")
            messagebox.showerror("Error", f"Failed to open timer: {str(e)}")

    def _close_timer_window(self, window):
        """Close timer window safely"""
        try:
            if hasattr(self.timer, 'timer_running') and self.timer.timer_running:
                result = messagebox.askquestion("Timer Running",
                                                "Timer is still running. Stop and return to dashboard?")
                if result == 'yes':
                    self.timer.stop_timer()
                    window.destroy()
            else:
                window.destroy()
        except Exception as e:
            print(f"ERROR closing timer window: {e}")
            try:
                window.destroy()
            except:
                pass

    def update_timer_display(self, time_left):
        """Update timer display"""
        try:
            if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                formatted_time = format_time(time_left)
                self.time_label.config(text=formatted_time)

                progress = self.timer.get_progress_percentage()
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.set_progress(progress)
        except Exception as e:
            print(f"ERROR updating timer display: {e}")

    def on_session_complete(self, completed):
        """Handle session completion"""
        try:
            session_info = self.timer.get_session_info()
            if hasattr(self, 'session_label') and self.session_label.winfo_exists():
                self.session_label.config(
                    text=session_info['title'], fg=session_info['color'])

            if hasattr(self, 'time_label') and self.time_label.winfo_exists():
                self.time_label.config(bg=session_info['color'])

            if hasattr(self, 'stats_label') and self.stats_label.winfo_exists():
                self.stats_label.config(
                    text=f"Sessions Completed Today: {self.timer.session_count}")
        except Exception as e:
            print(f"ERROR in on_session_complete: {e}")

    def on_timer_state_change(self, state):
        """Handle timer state changes"""
        try:
            if not hasattr(self, 'start_btn') or not self.start_btn.winfo_exists():
                return

            if state == "started":
                self.start_btn.config(state='disabled')
                if hasattr(self, 'pause_btn'):
                    self.pause_btn.config(state='normal')
            elif state == "paused":
                if hasattr(self, 'pause_btn'):
                    self.pause_btn.config(text="Resume")
            elif state == "resumed":
                if hasattr(self, 'pause_btn'):
                    self.pause_btn.config(text="Pause")
            elif state == "stopped":
                self.start_btn.config(state='normal')
                if hasattr(self, 'pause_btn'):
                    self.pause_btn.config(state='disabled', text="Pause")
        except Exception as e:
            print(f"ERROR in on_timer_state_change: {e}")

    def show_history_window(self):
        """Show session history with FIXED database retrieval"""
        # COMPREHENSIVE DEBUG FOR HISTORY ISSUE
        print(f"\nDEBUG: ===== HISTORY WINDOW DEBUG START =====")
        print(f"DEBUG: Opening history for user: '{self.current_user}'")

        # Debug database directly
        self.debug_database_for_user("history")

        # Test get_session_history method specifically
        try:
            print(
                f"DEBUG: Testing db.get_session_history('{self.current_user}', 50)")
            history, message = self.db.get_session_history(
                self.current_user, 50)
            print(
                f"DEBUG: get_session_history returned {len(history)} records")
            print(f"DEBUG: Message: '{message}'")

            if history:
                print(f"DEBUG: First few history records:")
                for i, record in enumerate(history[:3]):
                    print(f"  Record {i}: {record}")
            else:
                print(f"DEBUG: get_session_history returned EMPTY!")

                # Try alternative query to see if it's a method issue
                try:
                    conn = self.db.get_connection()
                    cursor = conn.cursor()

                    # Try case-insensitive search
                    cursor.execute(
                        "SELECT start_time, duration_minutes, session_type, completed FROM pomodoro_logs WHERE LOWER(username) = LOWER(?) ORDER BY start_time DESC LIMIT 50", (self.current_user,))
                    alt_history = cursor.fetchall()
                    print(
                        f"DEBUG: Alternative query found {len(alt_history)} records")

                    if alt_history:
                        print(f"DEBUG: Alternative query results:")
                        for record in alt_history[:3]:
                            print(f"  Alt Record: {record}")

                    conn.close()

                except Exception as e:
                    print(f"DEBUG: Alternative query failed: {e}")

        except Exception as e:
            print(f"DEBUG: get_session_history failed with error: {e}")

        print(f"DEBUG: ===== HISTORY WINDOW DEBUG END =====\n")

        try:
            history_window = tk.Toplevel(self.current_window)
            history_window.title("Session History")
            history_window.configure(bg=COLORS['background'])
            history_window.grab_set()

            # Better history window sizing
            history_window.resizable(True, True)
            history_window.minsize(650, 500)

            # Get screen size for better sizing
            screen_width = history_window.winfo_screenwidth()
            screen_height = history_window.winfo_screenheight()

            window_width = min(750, int(screen_width * 0.5))
            window_height = min(550, int(screen_height * 0.65))
            self.center_window_perfectly(
                history_window, window_width, window_height)

            main_frame = tk.Frame(history_window, bg=COLORS['background'],
                                  padx=20, pady=15)
            main_frame.pack(expand=True, fill='both')

            # Enhanced title
            title_label = tk.Label(main_frame, text=f"{self.current_user}'s Study Journey",
                                   font=("Segoe UI", 16, "bold"), fg=COLORS['primary'],
                                   bg=COLORS['background'])
            title_label.pack(pady=15)

            # Enhanced quick stats
            stats, _ = self.db.get_user_stats(self.current_user)
            if stats:
                summary_frame = tk.Frame(main_frame, bg=COLORS['info'], relief='raised',
                                         bd=2, padx=15, pady=12)
                summary_frame.pack(fill='x', pady=8)

                total_hours = stats['total_minutes'] // 60
                total_mins = stats['total_minutes'] % 60
                stats_text = (f"Total: {stats['total_sessions']} sessions | "
                              f"{total_hours}h {total_mins}m studied | "
                              f"Avg: {stats['avg_duration']:.1f} min/session")

                tk.Label(summary_frame, text="Your Achievements",
                         font=FONTS['subheader'], bg=COLORS['info'], fg=COLORS['white']).pack()
                tk.Label(summary_frame, text=stats_text, font=FONTS['label'],
                         bg=COLORS['info'], fg=COLORS['white']).pack(pady=4)

            # Enhanced history list
            history_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                     bd=2, padx=15, pady=12)
            history_frame.pack(fill='both', expand=True, pady=12)

            tk.Label(history_frame, text="Recent Sessions", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, 8))

            # Enhanced listbox
            listbox_frame = tk.Frame(history_frame, bg=COLORS['white'])
            listbox_frame.pack(fill='both', expand=True)

            listbox = tk.Listbox(listbox_frame, font=FONTS['small'], height=12,
                                 bg=COLORS['light'], fg=COLORS['text'], relief='solid', bd=1)
            scrollbar = tk.Scrollbar(
                listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)

            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Get and display enhanced history - WITH FIXED RETRIEVAL
            try:
                # First try the normal method
                history, history_message = self.db.get_session_history(
                    self.current_user, 50)

                # If that fails, try a direct database query with case-insensitive search
                if not history:
                    print(
                        f"DEBUG: Normal history method returned empty, trying direct query...")
                    try:
                        conn = self.db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT start_time, duration_minutes, session_type, completed
                            FROM pomodoro_logs 
                            WHERE LOWER(username) = LOWER(?)
                            ORDER BY start_time DESC 
                            LIMIT 50
                        """, (self.current_user,))
                        history = cursor.fetchall()
                        conn.close()
                        print(
                            f"DEBUG: Direct query found {len(history)} records")
                    except Exception as e:
                        print(f"DEBUG: Direct query failed: {e}")
                        history = []

            except Exception as e:
                print(f"ERROR getting session history: {e}")
                history = []

            if history:
                print(
                    f"DEBUG: Displaying {len(history)} history records in UI")
                for record in history:
                    try:
                        date_time = record[0]
                        duration = record[1]
                        session_type = record[2]
                        completed = record[3]

                        # Parse date_time if it's a string
                        if isinstance(date_time, str):
                            try:
                                from datetime import datetime
                                date_time = datetime.fromisoformat(
                                    date_time.replace('Z', '+00:00'))
                            except:
                                pass

                        date_str = date_time.strftime(
                            "%Y-%m-%d %H:%M") if hasattr(date_time, 'strftime') else str(date_time)
                        status_text = "COMPLETED" if completed else "SKIPPED"

                        display_text = f"{status_text} | {date_str} | {duration} min | {session_type.upper()}"
                        listbox.insert(tk.END, display_text)
                    except Exception as e:
                        print(f"ERROR processing history record {record}: {e}")
                        continue
            else:
                listbox.insert(tk.END, "No session history found yet.")
                listbox.insert(
                    tk.END, "Complete your first session to see it here!")
                print(f"DEBUG: No history records to display")

            # Enhanced close button
            EnhancedButton(main_frame, text="Close",
                           command=history_window.destroy, button_type='danger',
                           width=12, height=2).pack(pady=12)

        except Exception as e:
            print(f"ERROR in show_history_window: {e}")
            messagebox.showerror("Error", f"Failed to load history: {str(e)}")

    def show_settings_window(self):
        """Show settings configuration with better window sizing"""
        try:
            settings_window = tk.Toplevel(self.current_window)
            settings_window.title("Settings")
            settings_window.configure(bg=COLORS['background'])
            settings_window.grab_set()

            # Better settings window sizing
            settings_window.resizable(True, True)
            settings_window.minsize(500, 450)

            # Get screen size for better sizing
            screen_width = settings_window.winfo_screenwidth()
            screen_height = settings_window.winfo_screenheight()

            window_width = min(550, int(screen_width * 0.4))
            window_height = min(500, int(screen_height * 0.55))
            self.center_window_perfectly(
                settings_window, window_width, window_height)

            main_frame = tk.Frame(settings_window, bg=COLORS['background'],
                                  padx=25, pady=20)
            main_frame.pack(expand=True, fill='both')

            # Enhanced title
            title_label = tk.Label(main_frame, text="Pomodoro Settings",
                                   font=("Segoe UI", 16, "bold"), fg=COLORS['info'],
                                   bg=COLORS['background'])
            title_label.pack(pady=15)

            # Enhanced Theme Settings
            theme_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                   bd=2, padx=20, pady=15)
            theme_frame.pack(fill='x', pady=8)

            tk.Label(theme_frame, text="Appearance", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, 12))

            theme_control_frame = tk.Frame(theme_frame, bg=COLORS['white'])
            theme_control_frame.pack(fill='x')

            tk.Label(theme_control_frame, text="Theme Mode:", font=FONTS['label'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(side=tk.LEFT)

            current_theme = "Dark Mode" if APP_STATE['dark_mode'] else "Light Mode"
            switch_to = "Light" if APP_STATE['dark_mode'] else "Dark"

            EnhancedButton(theme_control_frame, text=f"Switch to {switch_to}",
                           command=self.toggle_theme_from_settings,
                           button_type='info', width=16, height=1).pack(side=tk.RIGHT)

            tk.Label(theme_frame, text=f"Current: {current_theme}", font=FONTS['small'],
                     bg=COLORS['white'], fg=COLORS['text_secondary']).pack(pady=4)

            # Enhanced Timer Settings
            timer_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                   bd=2, padx=20, pady=15)
            timer_frame.pack(fill='x', pady=8)

            tk.Label(timer_frame, text="Timer Durations (minutes)", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, 12))

            # Enhanced duration controls
            durations_grid = tk.Frame(timer_frame, bg=COLORS['white'])
            durations_grid.pack(fill='x', pady=8)

            # Work duration
            work_frame = tk.Frame(durations_grid, bg=COLORS['white'])
            work_frame.pack(fill='x', pady=6)

            tk.Label(work_frame, text="Work Session:", font=FONTS['label'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(side=tk.LEFT)
            work_var = tk.StringVar(value=str(TIMER_CONFIG['work_time'] // 60))
            work_entry = tk.Entry(work_frame, textvariable=work_var, font=FONTS['label'],
                                  width=8, justify='center', relief='solid', bd=1)
            work_entry.pack(side=tk.RIGHT)

            # Break duration
            break_frame = tk.Frame(durations_grid, bg=COLORS['white'])
            break_frame.pack(fill='x', pady=6)

            tk.Label(break_frame, text="Short Break:", font=FONTS['label'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(side=tk.LEFT)
            break_var = tk.StringVar(
                value=str(TIMER_CONFIG['break_time'] // 60))
            break_entry = tk.Entry(break_frame, textvariable=break_var, font=FONTS['label'],
                                   width=8, justify='center', relief='solid', bd=1)
            break_entry.pack(side=tk.RIGHT)

            # Long break duration
            long_break_frame = tk.Frame(durations_grid, bg=COLORS['white'])
            long_break_frame.pack(fill='x', pady=6)

            tk.Label(long_break_frame, text="Long Break:", font=FONTS['label'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(side=tk.LEFT)
            long_break_var = tk.StringVar(
                value=str(TIMER_CONFIG['long_break_time'] // 60))
            long_break_entry = tk.Entry(long_break_frame, textvariable=long_break_var,
                                        font=FONTS['label'], width=8, justify='center',
                                        relief='solid', bd=1)
            long_break_entry.pack(side=tk.RIGHT)

            def save_timer_settings():
                try:
                    work_minutes = safe_int(work_var.get())
                    break_minutes = safe_int(break_var.get())
                    long_break_minutes = safe_int(long_break_var.get())

                    if not (5 <= work_minutes <= 60) or not (1 <= break_minutes <= 30) or not (5 <= long_break_minutes <= 60):
                        messagebox.showerror("Error",
                                             "Invalid time ranges!\n\n" +
                                             "Work: 5-60 min\n" +
                                             "Short Break: 1-30 min\n" +
                                             "Long Break: 5-60 min")
                        return

                    TIMER_CONFIG['work_time'] = work_minutes * 60
                    TIMER_CONFIG['break_time'] = break_minutes * 60
                    TIMER_CONFIG['long_break_time'] = long_break_minutes * 60

                    if self.timer:
                        self.timer.work_time = TIMER_CONFIG['work_time']
                        self.timer.break_time = TIMER_CONFIG['break_time']
                        self.timer.long_break_time = TIMER_CONFIG['long_break_time']

                    messagebox.showinfo(
                        "Success", "Timer settings saved successfully!")
                    settings_window.destroy()

                except Exception as e:
                    print(f"ERROR saving timer settings: {e}")
                    messagebox.showerror(
                        "Error", f"Failed to save settings: {str(e)}")

            # Enhanced action buttons
            button_frame = tk.Frame(main_frame, bg=COLORS['background'])
            button_frame.pack(pady=20)

            EnhancedButton(button_frame, text="Save Changes",
                           command=save_timer_settings, button_type='success',
                           width=13, height=2).pack(side=tk.LEFT, padx=6)

            EnhancedButton(button_frame, text="Cancel",
                           command=settings_window.destroy, button_type='danger',
                           width=13, height=2).pack(side=tk.LEFT, padx=6)

        except Exception as e:
            print(f"ERROR in show_settings_window: {e}")
            messagebox.showerror("Error", f"Failed to open settings: {str(e)}")

    def toggle_theme_from_settings(self):
        """Toggle theme from settings window"""
        try:
            toggle_theme()
            # Close all child windows
            for child in self.current_window.winfo_children():
                if isinstance(child, tk.Toplevel):
                    try:
                        child.destroy()
                    except:
                        pass

            # Refresh main window
            self.current_window.destroy()
            self.show_pomodoro_menu()
        except Exception as e:
            print(f"ERROR toggling theme: {e}")

    def back_to_main_menu(self):
        """Return to main menu"""
        try:
            if self.timer and hasattr(self.timer, 'timer_running') and self.timer.timer_running:
                result = messagebox.askquestion("Timer Running",
                                                "Timer is still running. Stop and return to main menu?")
                if result == 'no':
                    return

                self.timer.stop_timer()

            APP_STATE['running'] = False
            if self.current_window and self.current_window.winfo_exists():
                self.current_window.destroy()

            if self.return_callback:
                APP_STATE['running'] = True
                self.return_callback()
            else:
                sys.exit(0)

        except Exception as e:
            print(f"ERROR returning to main menu: {e}")
            messagebox.showerror(
                "Error", f"Failed to return to main menu: {str(e)}")

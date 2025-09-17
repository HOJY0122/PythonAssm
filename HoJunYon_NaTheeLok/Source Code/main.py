import atexit  # For registering cleanup functions to run on exit
import os  # For operating system interactions and file paths
import sys  # For system-specific parameters and functions
import tkinter as tk  # For GUI creation
from tkinter import messagebox  # For displaying message dialogs

# Import shared configuration and components
from shared.config import (APP_STATE, COLORS, FONTS, apply_theme_to_window,
                           cleanup_application, toggle_theme)
from shared.ui_components import EnhancedButton

# Import shared modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def check_requirements():
    """Check if all required dependencies are installed"""
    requirements_met = True
    missing_packages = []

    print("Checking system requirements...")

    # Check tkinter
    try:
        import tkinter
        print("✅ Tkinter GUI library available")
    except ImportError:
        print("❌ Tkinter not available")
        requirements_met = False
        missing_packages.append("tkinter")

    # Check SQLite3
    try:
        import sqlite3
        print("✅ SQLite3 database available")
    except ImportError:
        print("❌ SQLite3 not available")
        requirements_met = False
        missing_packages.append("sqlite3")

    # Check hashlib and secrets
    try:
        import hashlib
        import secrets
        print("✅ Security modules available (hashlib, secrets)")
    except ImportError:
        print("❌ Security modules not available")
        requirements_met = False
        missing_packages.append("hashlib/secrets")

    # Check optional dependencies
    try:
        import pygame
        print("✅ Pygame available (enhanced sound notifications)")
    except ImportError:
        print("○ Pygame not available (basic sound notifications only)")
        print("  Optional: pip install pygame for better sound")

    # Handle missing requirements
    if not requirements_met:
        error_msg = f"Missing required packages: {', '.join(missing_packages)}"
        # Create error message
        try:
            messagebox.showerror("Missing Dependencies",
                                 f"Required packages are missing:\n\n" +
                                 "\n".join([f"• {pkg}" for pkg in missing_packages]) +
                                 "\n\nPlease install the missing packages and try again.")
        except:
            pass
        return False

    return True


class MainMenuApp:
    """Main menu application for TAR UMT Student Assistant"""

    def __init__(self):
        self.root = None  # Main application window
        self.current_app = None  # Currently running sub-application
        self.current_user = None  # Currently logged in user
        self.db = None  # Database connection

        # Initialize database connection
        try:
            from shared.database import PomodoroDatabase  # Import database class
            self.db = PomodoroDatabase()  # Create database instance
            APP_STATE['database'] = self.db  # Store database in global state
        except Exception as e:
            messagebox.showerror(
                "Database Error", f"Failed to connect to database: {str(e)}")
            return

        # Start with login page
        self.show_login_page()

    def center_window_perfectly(self, window, width, height):
        """Center the window on the screen with better accuracy"""
        # Force window to update so we get accurate screen dimensions
        window.update_idletasks()

        # Get ACTUAL screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        print(f"DEBUG: Screen size: {screen_width}x{screen_height}")
        print(f"DEBUG: Window size: {width}x{height}")

        # Calculate EXACT center position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Adjust for taskbar (move slightly up)
        y = max(0, y - 30)

        print(f"DEBUG: Calculated position: x={x}, y={y}")

        # Set window geometry with EXACT position
        geometry_string = f"{width}x{height}+{x}+{y}"
        print(f"DEBUG: Setting geometry: {geometry_string}")

        window.geometry(geometry_string)

        # Additional centering steps
        window.update_idletasks()

        # Force window to the calculated position
        window.wm_geometry(geometry_string)

        # Bring window to front and focus
        window.lift()
        window.focus_force()

        # Additional verification
        window.after(100, lambda: self._verify_centering(window, x, y))

    def _verify_centering(self, window, expected_x, expected_y):
        """Verify and correct window position if needed"""
        try:
            actual_x = window.winfo_x()
            actual_y = window.winfo_y()
            print(f"DEBUG: Expected position: ({expected_x}, {expected_y})")
            print(f"DEBUG: Actual position: ({actual_x}, {actual_y})")

            # If position is significantly off, correct it
            if abs(actual_x - expected_x) > 50 or abs(actual_y - expected_y) > 50:
                print("DEBUG: Position correction needed")
                geometry_string = f"+{expected_x}+{expected_y}"
                window.geometry(geometry_string)
        except:
            pass  # Ignore errors in verification

    def get_optimal_window_size(self, min_width=1000, min_height=700):
        """Get optimal window size for better desktop experience"""
        # Create a temporary window to get screen size if root doesn't exist yet
        if not self.root or not self.root.winfo_exists():
            temp_root = tk.Tk()
            temp_root.withdraw()  # Hide it
            screen_width = temp_root.winfo_screenwidth()
            screen_height = temp_root.winfo_screenheight()
            temp_root.destroy()
        else:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

        print(f"DEBUG: Screen dimensions: {screen_width}x{screen_height}")

        # Calculate reasonable window size (not too big, not too small)
        if screen_width >= 1920:
            width_percent = 0.6
            height_percent = 0.7
        else:
            width_percent = 0.75
            height_percent = 0.8

        optimal_width = max(min_width, int(screen_width * width_percent))
        optimal_height = max(min_height, int(screen_height * height_percent))

        print(f"DEBUG: Optimal window size: {optimal_width}x{optimal_height}")

        return optimal_width, optimal_height

    def show_login_page(self):
        """Display the login page for user authentication"""
        try:
            print("DEBUG: Creating login page...")

            # Clean up any existing window safely
            if self.root and self.root.winfo_exists():
                self.root.destroy()
            self.root = None

            self.root = tk.Tk()
            self.root.title("TAR UMT Student Assistant - Login")
            apply_theme_to_window(self.root)
            self.root.resizable(True, True)
            self.root.minsize(1000, 700)

            # Get optimal size and center it properly
            window_width, window_height = self.get_optimal_window_size(
                1000, 700)

            # FIXED: Use the corrected centering function
            self.center_window_perfectly(
                self.root, window_width, window_height)

            # Create scrollable container for login page
            main_canvas = tk.Canvas(self.root, bg=COLORS['background'])
            main_scrollbar = tk.Scrollbar(
                self.root, orient="vertical", command=main_canvas.yview)
            scrollable_frame = tk.Frame(main_canvas, bg=COLORS['background'])

            scrollable_frame.bind(
                "<Configure>",
                lambda e: main_canvas.configure(
                    scrollregion=main_canvas.bbox("all"))
            )

            main_canvas.create_window(
                (window_width // 2+30, 0), window=scrollable_frame, anchor="n")
            main_canvas.configure(yscrollcommand=main_scrollbar.set)

            # Pack canvas and scrollbar
            main_canvas.pack(side="left", fill="both", expand=True)
            main_scrollbar.pack(side="right", fill="y")

            # Mouse wheel scrolling support
            def _on_mousewheel(event):
                main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

            # Padding to fill the window
            padding_x = max(80, int(window_width * 0.08))
            padding_y = max(60, int(window_height * 0.08))
            main_frame = tk.Frame(scrollable_frame, bg=COLORS['background'],
                                  padx=padding_x, pady=padding_y)
            main_frame.pack(expand=True, fill='both')

            # Header section
            self._create_login_header(main_frame, window_width, window_height)

            # Login form section
            self._create_login_form(main_frame, window_width, window_height)

            # Footer section
            self._create_login_footer(main_frame, window_width, window_height)

            # Setup exit protocol
            self.root.protocol("WM_DELETE_WINDOW", self.exit_application)

            # Focus on username entry
            if hasattr(self, 'username_entry'):
                self.username_entry.focus()

            print("DEBUG: Login page created, starting mainloop...")
            self.root.mainloop()

        except Exception as e:
            print(f"ERROR creating login page: {e}")
            messagebox.showerror(
                "Error", f"Failed to create login page: {str(e)}")

    def _create_login_header(self, parent, window_width, window_height):
        """Create login page header"""
        header_frame = tk.Frame(parent, bg=COLORS['background'])
        header_frame.pack(fill='x', pady=(
            0, max(20, int(window_height * 0.03))))

        logo_size = min(60, max(40, int(window_width * 0.04)))
        logo_label = tk.Label(header_frame, text="📚", font=("Segoe UI", logo_size),
                              bg=COLORS['background'], fg=COLORS['primary'])
        logo_label.pack(pady=max(10, int(window_height * 0.015)))

        title_size = min(32, max(20, int(window_width * 0.025)))
        title_label = tk.Label(header_frame, text="TAR UMT Student Assistant",
                               font=("Segoe UI", title_size, "bold"),
                               fg=COLORS['primary'], bg=COLORS['background'])
        title_label.pack(pady=max(8, int(window_height * 0.01)))

        subtitle_size = min(16, max(11, int(window_width * 0.012)))
        subtitle_label = tk.Label(header_frame, text="Please sign in to continue",
                                  font=("Segoe UI", subtitle_size),
                                  fg=COLORS['text_secondary'], bg=COLORS['background'])
        subtitle_label.pack(pady=max(5, int(window_height * 0.008)))

    def _create_login_form(self, parent, window_width, window_height):
        """Create login form"""
        form_padding_x = max(50, int(window_width * 0.08))
        form_padding_y = max(25, int(window_height * 0.035))

        form_frame = tk.Frame(parent, bg=COLORS['white'], relief='raised',
                              bd=2, padx=form_padding_x, pady=form_padding_y)
        form_frame.pack(fill='x', pady=max(15, int(window_height * 0.02)))

        title_size = min(20, max(16, int(window_width * 0.016)))
        tk.Label(form_frame, text="Sign In", font=("Segoe UI", title_size, "bold"),
                 bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, max(20, int(window_height * 0.03))))

        username_frame = tk.Frame(form_frame, bg=COLORS['white'])
        username_frame.pack(fill='x', pady=max(10, int(window_height * 0.015)))

        label_size = min(14, max(11, int(window_width * 0.01)))

        tk.Label(username_frame, text="Username:", font=("Segoe UI", label_size),
                 bg=COLORS['white'], fg=COLORS['text']).pack(anchor='w', pady=(0, 5))

        entry_font_size = min(12, max(10, int(window_width * 0.009)))
        entry_padding = max(8, int(window_height * 0.01))
        self.username_entry = tk.Entry(username_frame, font=("Segoe UI", entry_font_size),
                                       relief='solid', bd=1, bg=COLORS['light'],
                                       fg=COLORS['text'])
        self.username_entry.pack(fill='x', ipady=entry_padding)

        password_frame = tk.Frame(form_frame, bg=COLORS['white'])
        password_frame.pack(fill='x', pady=max(10, int(window_height * 0.015)))

        tk.Label(password_frame, text="Password:", font=("Segoe UI", label_size),
                 bg=COLORS['white'], fg=COLORS['text']).pack(anchor='w', pady=(0, 5))

        self.password_entry = tk.Entry(password_frame, show="*", font=("Segoe UI", entry_font_size),
                                       relief='solid', bd=1, bg=COLORS['light'],
                                       fg=COLORS['text'])
        self.password_entry.pack(fill='x', ipady=entry_padding)

        login_btn_frame = tk.Frame(form_frame, bg=COLORS['white'])
        login_btn_frame.pack(pady=max(20, int(window_height * 0.03)))

        button_width = max(25, min(35, int(window_width * 0.03)))
        button_height = max(2, min(3, int(window_height * 0.005)))
        EnhancedButton(login_btn_frame, text="Sign In",
                       command=self.attempt_login, button_type='primary',
                       width=button_width, height=button_height).pack(pady=5)

        register_frame = tk.Frame(form_frame, bg=COLORS['white'])
        register_frame.pack(pady=max(15, int(window_height * 0.02)))

        reg_label_size = min(11, max(9, int(window_width * 0.008)))
        tk.Label(register_frame, text="Don't have an account?", font=("Segoe UI", reg_label_size),
                 bg=COLORS['white'], fg=COLORS['text_secondary']).pack()

        reg_button_width = max(22, min(30, int(window_width * 0.025)))
        reg_button_height = max(1, min(2, int(window_height * 0.003)))
        EnhancedButton(register_frame, text="Create New Account",
                       command=self.show_register_window, button_type='success',
                       width=reg_button_width, height=reg_button_height).pack(pady=8)

        self.username_entry.bind('<Return>', lambda e: self.attempt_login())
        self.password_entry.bind('<Return>', lambda e: self.attempt_login())

    def _create_login_footer(self, parent, window_width, window_height):
        """Create login page footer"""
        footer_frame = tk.Frame(parent, bg=COLORS['background'])
        footer_frame.pack(fill='x', pady=max(30, int(window_height * 0.04)))

        theme_button_width = max(20, min(30, int(window_width * 0.02)))
        theme_button_height = max(2, min(3, int(window_height * 0.004)))
        theme_text = "🌙 Dark Mode" if not APP_STATE['dark_mode'] else "☀️ Light Mode"
        theme_btn = EnhancedButton(footer_frame, text=theme_text,
                                   command=self.toggle_theme, button_type='info',
                                   width=theme_button_width, height=theme_button_height)
        theme_btn.pack(pady=20)

        info_padding = max(40, int(window_width * 0.03))
        info_frame = tk.Frame(parent, bg=COLORS['info'], relief='raised',
                              bd=2, padx=info_padding, pady=max(25, int(window_height * 0.03)))
        info_frame.pack(fill='x', pady=20)

        info_title_size = min(16, max(11, int(window_width * 0.012)))
        tk.Label(info_frame, text="TAR UMT Student Productivity Suite",
                 font=("Segoe UI", info_title_size, "bold"),
                 bg=COLORS['info'], fg=COLORS['white']).pack(pady=5)

        info_text_size = min(12, max(9, int(window_width * 0.009)))
        tk.Label(info_frame, text="Developed by HO JUN YON and NA THEE LOK",
                 font=("Segoe UI", info_text_size), bg=COLORS['info'], fg=COLORS['white']).pack(pady=5)

    def attempt_login(self):
        """Attempt to authenticate user login"""
        try:
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()

            if not username or not password:
                messagebox.showerror(
                    "Error", "Please enter both username and password.")
                return

            # Show loading feedback
            self.username_entry.config(state='disabled')
            self.password_entry.config(state='disabled')

            # Authenticate with database
            success, message = self.db.authenticate_user(username, password)

            if success:
                self.current_user = username
                messagebox.showinfo(
                    "Welcome!", f"Login successful!\nWelcome back, {username}!")
                self.show_main_menu()
            else:
                messagebox.showerror("Login Failed", message)
                self.password_entry.delete(0, 'end')  # Clear password field

            # Re-enable entries
            self.username_entry.config(state='normal')
            self.password_entry.config(state='normal')

        except Exception as e:
            # error handling
            self.username_entry.config(state='normal')
            self.password_entry.config(state='normal')
            messagebox.showerror("Error", f"Login failed: {str(e)}")

    def show_register_window(self):
        """Show registration window for new users"""
        try:
            register_window = tk.Toplevel(self.root)
            register_window.title("Create New Account")
            register_window.configure(bg=COLORS['background'])
            register_window.resizable(True, True)
            register_window.grab_set()

            main_width = self.root.winfo_width()
            main_height = self.root.winfo_height()

            window_width = max(600, int(main_width * 0.5))
            window_height = max(700, int(main_height * 0.7))
            self.center_window_perfectly(
                register_window, window_width, window_height)

            padding = max(50, int(window_width * 0.08))
            main_frame = tk.Frame(register_window, bg=COLORS['background'],
                                  padx=padding, pady=padding)
            main_frame.pack(expand=True, fill='both')

            title_size = min(24, max(16, int(window_width * 0.04)))
            title_label = tk.Label(main_frame, text="Create Your Account",
                                   font=("Segoe UI", title_size, "bold"), fg=COLORS['success'],
                                   bg=COLORS['background'])
            title_label.pack(pady=max(25, int(window_height * 0.04)))

            form_padding = max(40, int(window_width * 0.08))
            form_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                  bd=3, padx=form_padding, pady=form_padding)
            form_frame.pack(fill='x')

            label_size = min(16, max(12, int(window_width * 0.025)))
            entry_size = min(14, max(11, int(window_width * 0.02)))
            entry_padding = max(12, int(window_height * 0.02))

            # Username field
            tk.Label(form_frame, text="Choose Username:", font=("Segoe UI", label_size),
                     bg=COLORS['white'], fg=COLORS['text']).pack(anchor='w', pady=(15, 8))
            username_entry = tk.Entry(form_frame, font=("Segoe UI", entry_size),
                                      relief='solid', bd=2, bg=COLORS['light'])
            username_entry.pack(fill='x', ipady=entry_padding, pady=(0, 20))

            # Password field
            tk.Label(form_frame, text="Create Password:", font=("Segoe UI", label_size),
                     bg=COLORS['white'], fg=COLORS['text']).pack(anchor='w', pady=(10, 8))
            password_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", entry_size),
                                      relief='solid', bd=2, bg=COLORS['light'])
            password_entry.pack(fill='x', ipady=entry_padding, pady=(0, 20))

            # Confirm Password field
            tk.Label(form_frame, text="Confirm Password:", font=("Segoe UI", label_size),
                     bg=COLORS['white'], fg=COLORS['text']).pack(anchor='w', pady=(10, 8))
            confirm_entry = tk.Entry(form_frame, show="*", font=("Segoe UI", entry_size),
                                     relief='solid', bd=2, bg=COLORS['light'])
            confirm_entry.pack(fill='x', ipady=entry_padding, pady=(0, 30))

            def register_user():
                try:
                    username = username_entry.get().strip()
                    password = password_entry.get().strip()
                    confirm = confirm_entry.get().strip()

                    if not username or not password or not confirm:
                        messagebox.showerror(
                            "Error", "Please fill in all fields.")
                        return

                    if password != confirm:
                        messagebox.showerror(
                            "Error", "Passwords do not match.")
                        return

                    # Disable buttons during registration
                    username_entry.config(state='disabled')
                    password_entry.config(state='disabled')
                    confirm_entry.config(state='disabled')

                    success, message = self.db.register_user(
                        username, password)

                    if success:
                        messagebox.showinfo("Success", f"{message}")
                        register_window.destroy()
                    else:
                        messagebox.showerror("Registration Failed", message)
                        # Re-enable entries
                        username_entry.config(state='normal')
                        password_entry.config(state='normal')
                        confirm_entry.config(state='normal')

                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Registration failed: {str(e)}")

            # Enter key bindings for registration
            username_entry.bind('<Return>', lambda e: password_entry.focus())
            password_entry.bind('<Return>', lambda e: confirm_entry.focus())
            confirm_entry.bind('<Return>', lambda e: register_user())

            button_frame = tk.Frame(form_frame, bg=COLORS['white'])
            button_frame.pack(pady=25)

            button_width = max(18, min(25, int(window_width * 0.04)))
            button_height = max(2, min(4, int(window_height * 0.006)))

            EnhancedButton(button_frame, text="Create Account",
                           command=register_user, button_type='success',
                           width=button_width, height=button_height).pack(side=tk.LEFT, padx=10)

            EnhancedButton(button_frame, text="Cancel",
                           command=register_window.destroy, button_type='danger',
                           width=max(12, int(button_width * 0.7)), height=button_height).pack(side=tk.LEFT, padx=10)

            # Focus on username
            username_entry.focus()

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to open registration: {str(e)}")

    def show_main_menu(self):
        """Display the main menu"""
        try:
            print("DEBUG: Creating main menu...")

            # Clean up any existing window safely
            if self.root and self.root.winfo_exists():
                self.root.destroy()
            self.root = None

            self.root = tk.Tk()
            self.root.title("TAR UMT Student Assistant")
            apply_theme_to_window(self.root)
            self.root.resizable(True, True)
            self.root.minsize(1000, 650)

            # Get optimal size and center properly
            window_width, window_height = self.get_optimal_window_size(
                1000, 650)

            # FIXED: Use the corrected centering function
            self.center_window_perfectly(
                self.root, window_width, window_height)

            main_canvas = tk.Canvas(self.root, bg=COLORS['background'])
            main_scrollbar = tk.Scrollbar(
                self.root, orient="vertical", command=main_canvas.yview)
            scrollable_frame = tk.Frame(main_canvas, bg=COLORS['background'])

            scrollable_frame.bind(
                "<Configure>",
                lambda e: main_canvas.configure(
                    scrollregion=main_canvas.bbox("all"))
            )

            main_canvas.create_window(
                (window_width // 2+60, 0), window=scrollable_frame, anchor="n")
            main_canvas.configure(yscrollcommand=main_scrollbar.set)

            main_canvas.pack(side="left", fill="both", expand=True)
            main_scrollbar.pack(side="right", fill="y")

            def _on_mousewheel(event):
                main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

            main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

            padding_x = max(80, int(window_width * 0.06))
            padding_y = max(60, int(window_height * 0.06))
            main_frame = tk.Frame(scrollable_frame, bg=COLORS['background'],
                                  padx=padding_x, pady=padding_y)
            main_frame.pack(expand=True, fill='both')

            # Header section
            self._create_header(main_frame, window_width, window_height)

            # Applications section
            self._create_apps_section(main_frame, window_width, window_height)

            # Footer section
            self._create_footer(main_frame, window_width, window_height)

            # Setup exit protocol
            self.root.protocol("WM_DELETE_WINDOW", self.exit_application)

            print("DEBUG: Main menu created, starting mainloop...")
            self.root.mainloop()

        except Exception as e:
            print(f"ERROR creating main menu: {e}")
            messagebox.showerror(
                "Error", f"Failed to create main menu: {str(e)}")

    def _create_header(self, parent, window_width, window_height):
        """Create header section"""
        header_frame = tk.Frame(parent, bg=COLORS['background'])
        header_frame.pack(fill='x', pady=(
            0, max(30, int(window_height * 0.04))))

        # User welcome section with logout button
        user_frame = tk.Frame(header_frame, bg=COLORS['background'])
        user_frame.pack(fill='x', pady=(0, max(15, int(window_height * 0.02))))

        logout_width = max(12, min(16, int(window_width * 0.012)))
        logout_height = max(1, min(2, int(window_height * 0.003)))
        EnhancedButton(user_frame, text="Logout",
                       command=self.logout, button_type='dark',
                       width=logout_width, height=logout_height).pack(side='right')

        welcome_frame = tk.Frame(header_frame, bg=COLORS['background'])
        welcome_frame.pack(fill='x', pady=(
            0, max(15, int(window_height * 0.02))))

        # welcome text
        welcome_size = min(22, max(16, int(window_width * 0.015)))
        welcome_text = f"Welcome back, {self.current_user}!" if self.current_user else "Welcome!"
        welcome_label = tk.Label(welcome_frame, text=welcome_text,
                                 font=("Segoe UI", welcome_size, "bold"),
                                 fg=COLORS['success'], bg=COLORS['background'])
        welcome_label.pack(anchor='center')

        # main title
        title_size = min(32, max(24, int(window_width * 0.02)))
        title_label = tk.Label(header_frame, text="TAR UMT Student Assistant",
                               font=("Segoe UI", title_size, "bold"),
                               fg=COLORS['primary'], bg=COLORS['background'])
        title_label.pack(pady=max(12, int(window_height * 0.015)))

        subtitle_size = min(16, max(12, int(window_width * 0.01)))
        subtitle_label = tk.Label(header_frame, text="Boost Your Academic Success with Productivity Tools",
                                  font=("Segoe UI", subtitle_size, "italic"),
                                  fg=COLORS['text_secondary'], bg=COLORS['background'])
        subtitle_label.pack(pady=max(8, int(window_height * 0.012)))

    def _create_apps_section(self, parent, window_width, window_height):
        """Create applications section"""
        content_frame = tk.Frame(parent, bg=COLORS['background'])
        content_frame.pack(expand=True, fill='both',
                           pady=max(25, int(window_height * 0.03)))

        apps_padding_x = max(50, int(window_width * 0.05))
        apps_padding_y = max(35, int(window_height * 0.045))

        apps_frame = tk.Frame(content_frame, bg=COLORS['white'], relief='raised',
                              bd=2, padx=apps_padding_x, pady=apps_padding_y)
        apps_frame.pack(fill='both', expand=True)

        # section title
        section_title_size = min(26, max(18, int(window_width * 0.018)))
        section_title = tk.Label(apps_frame, text="Choose Your Productivity Tool",
                                 font=("Segoe UI", section_title_size, "bold"),
                                 bg=COLORS['white'], fg=COLORS['text'])
        section_title.pack(pady=(0, max(30, int(window_height * 0.04))))

        # application cards grid
        cards_frame = tk.Frame(apps_frame, bg=COLORS['white'])
        cards_frame.pack(expand=True, fill='both')

        # Create cards
        self._create_pomodoro_card(cards_frame, window_width, window_height)
        self._create_reminder_card(cards_frame, window_width, window_height)

        # Configure grid weights
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

    def _create_pomodoro_card(self, parent, window_width, window_height):
        """Create Pomodoro Timer card"""
        # card padding
        card_padding_x = max(35, int(window_width * 0.025))
        card_padding_y = max(25, int(window_height * 0.03))
        grid_padding_x = max(20, int(window_width * 0.015))
        grid_padding_y = max(15, int(window_height * 0.02))

        pomodoro_card = tk.Frame(parent, bg=COLORS['light'], relief='raised',
                                 bd=2, padx=card_padding_x, pady=card_padding_y)
        pomodoro_card.grid(row=0, column=0, padx=grid_padding_x,
                           pady=grid_padding_y, sticky='nsew')

        # card header
        header_size = min(20, max(16, int(window_width * 0.014)))
        tk.Label(pomodoro_card, text="🍅 TIMER", font=("Segoe UI", header_size, "bold"),
                 bg=COLORS['light'], fg=COLORS['accent']).pack(pady=max(15, int(window_height * 0.02)))

        # card title
        title_size = min(18, max(14, int(window_width * 0.012)))
        tk.Label(pomodoro_card, text="Pomodoro Study Timer",
                 font=("Segoe UI", title_size, "bold"),
                 bg=COLORS['light'], fg=COLORS['text']).pack(pady=max(8, int(window_height * 0.01)))

        # description with readable text
        desc_size = min(12, max(10, int(window_width * 0.009)))
        description_text = """Enhanced productivity timer using the Pomodoro Technique

• Focus sessions with customizable breaks
• Comprehensive progress tracking & analytics  
• Secure user accounts & detailed session history
• Fully customizable timer settings & themes
• Advanced notification system with sound alerts"""

        wrap_length = max(300, int(window_width * 0.22))
        tk.Label(pomodoro_card, text=description_text,
                 font=("Segoe UI", desc_size), bg=COLORS['light'],
                 fg=COLORS['text_secondary'], justify='center',
                 wraplength=wrap_length).pack(pady=max(15, int(window_height * 0.02)))

        # launch button
        button_width = max(25, min(32, int(window_width * 0.022)))
        button_height = max(2, min(3, int(window_height * 0.004)))
        EnhancedButton(pomodoro_card, text="Launch Pomodoro Timer",
                       command=self.open_pomodoro_app, button_type='primary',
                       width=button_width, height=button_height).pack(pady=max(20, int(window_height * 0.025)))

    def _create_reminder_card(self, parent, window_width, window_height):
        """Create Reminder card"""
        card_padding_x = max(35, int(window_width * 0.025))
        card_padding_y = max(25, int(window_height * 0.03))
        grid_padding_x = max(20, int(window_width * 0.015))
        grid_padding_y = max(15, int(window_height * 0.02))

        reminder_card = tk.Frame(parent, bg=COLORS['light'], relief='raised',
                                 bd=2, padx=card_padding_x, pady=card_padding_y)
        reminder_card.grid(row=0, column=1, padx=grid_padding_x,
                           pady=grid_padding_y, sticky='nsew')

        # card header
        header_size = min(20, max(16, int(window_width * 0.014)))
        tk.Label(reminder_card, text="⏰ REMINDER", font=("Segoe UI", header_size, "bold"),
                 bg=COLORS['light'], fg=COLORS['success']).pack(pady=max(15, int(window_height * 0.02)))

        # card title
        title_size = min(18, max(14, int(window_width * 0.012)))
        tk.Label(reminder_card, text="Smart Reminder System",
                 font=("Segoe UI", title_size, "bold"),
                 bg=COLORS['light'], fg=COLORS['text']).pack(pady=max(8, int(window_height * 0.01)))

        # description
        desc_size = min(12, max(10, int(window_width * 0.009)))
        description_text = """Never miss important tasks and deadlines again

• Time-based alert notifications with sound
• Advanced categorized reminder organization
• Powerful search and filter functionality
• Beautiful calendar view with reminder indicators  
• Real-time clock display with date tracking"""

        wrap_length = max(300, int(window_width * 0.22))
        tk.Label(reminder_card, text=description_text,
                 font=("Segoe UI", desc_size), bg=COLORS['light'],
                 fg=COLORS['text_secondary'], justify='center',
                 wraplength=wrap_length).pack(pady=max(15, int(window_height * 0.02)))

        # launch button
        button_width = max(25, min(32, int(window_width * 0.022)))
        button_height = max(2, min(3, int(window_height * 0.004)))
        EnhancedButton(reminder_card, text="Launch Reminder App",
                       command=self.open_reminder_app, button_type='success',
                       width=button_width, height=button_height).pack(pady=max(20, int(window_height * 0.025)))

    def _create_footer(self, parent, window_width, window_height):
        """Create footer section"""
        footer_frame = tk.Frame(parent, bg=COLORS['background'])
        footer_frame.pack(fill='x', pady=max(40, int(window_height * 0.05)))
        # theme toggle button
        controls_frame = tk.Frame(footer_frame, bg=COLORS['background'])
        controls_frame.pack()

        theme_width = max(25, min(35, int(window_width * 0.025)))
        theme_height = max(2, min(4, int(window_height * 0.005)))
        theme_text = "🌙 Dark Mode" if not APP_STATE['dark_mode'] else "☀️ Light Mode"
        theme_btn = EnhancedButton(controls_frame, text=theme_text,
                                   command=self.toggle_theme, button_type='info',
                                   width=theme_width, height=theme_height)
        theme_btn.pack(pady=max(20, int(window_height * 0.025)))

        # info footer
        info_padding = max(50, int(window_width * 0.04))
        info_frame = tk.Frame(parent, bg=COLORS['info'], relief='raised',
                              bd=2, padx=info_padding, pady=max(30, int(window_height * 0.04)))
        info_frame.pack(fill='x', pady=max(20, int(window_height * 0.025)))

        info_title_size = min(18, max(12, int(window_width * 0.015)))
        tk.Label(info_frame, text="Developed by HO JUN YON and NA THEE LOK",
                 font=("Segoe UI", info_title_size, "bold"),
                 bg=COLORS['info'], fg=COLORS['white']).pack(pady=8)

        info_text_size = min(14, max(10, int(window_width * 0.01)))
        tk.Label(info_frame, text="AMCS1034 Software Development Fundamentals - TAR UMT Student Assistant Project",
                 font=("Segoe UI", info_text_size), bg=COLORS['info'], fg=COLORS['white'],
                 wraplength=max(1000, int(window_width * 0.7)),
                 justify='center').pack(pady=5)

    def open_pomodoro_app(self):
        """Launch the Pomodoro Timer application"""
        try:
            # loading feedback
            print(f"Launching Pomodoro Timer for user: {self.current_user}")

            # Safely destroy and clear reference
            if self.root and self.root.winfo_exists():
                self.root.destroy()
            self.root = None

            # Import and launch Pomodoro app with current user
            from pomodoro_app import PomodoroApp
            self.current_app = PomodoroApp(current_user=self.current_user,
                                           return_callback=self.show_main_menu)

        except ImportError as e:
            messagebox.showerror("Import Error",
                                 f"Failed to import Pomodoro app: {str(e)}\n\n" +
                                 "Make sure pomodoro_app.py is in the same directory.")
            self.show_main_menu()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to launch Pomodoro app: {str(e)}")
            self.show_main_menu()

    def open_reminder_app(self):
        """Launch the Simple Reminder application"""
        try:
            # Better loading feedback
            print(f"Launching Reminder App for user: {self.current_user}")

            # Safely destroy and clear reference
            if self.root and self.root.winfo_exists():
                self.root.destroy()
            self.root = None

            # Import and launch Reminder app with current user
            from reminder_app import ReminderApp
            self.current_app = ReminderApp(current_user=self.current_user,
                                           return_callback=self.show_main_menu)

        except ImportError as e:
            messagebox.showerror("Import Error",
                                 f"Failed to import Reminder app: {str(e)}\n\n" +
                                 "Make sure reminder_app.py is in the same directory.")
            self.show_main_menu()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to launch Reminder app: {str(e)}")
            self.show_main_menu()

    def logout(self):
        """Logout current user and return to login page"""
        try:
            result = messagebox.askquestion("Logout Confirmation",
                                            f"Are you sure you want to logout?\n\n" +
                                            f"User: {self.current_user}")
            if result == 'yes':
                self.current_user = None
                messagebox.showinfo(
                    "Goodbye!", f"You have been logged out successfully.\nThank you for using TAR UMT Student Assistant!")
                self.show_login_page()

        except Exception as e:
            messagebox.showerror("Error", f"Logout failed: {str(e)}")

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        try:
            toggle_theme()
            if self.current_user:
                self.show_main_menu()  # Refresh main menu if logged in
            else:
                self.show_login_page()  # Refresh login page if not logged in
        except Exception as e:
            messagebox.showerror("Error", f"Theme toggle failed: {str(e)}")

    def exit_application(self):
        """Exit the application with confirmation"""
        try:
            result = messagebox.askquestion("Exit Application",
                                            "Are you sure you want to exit TAR UMT Student Assistant?")
            if result == 'yes':
                cleanup_application()
                if self.root and self.root.winfo_exists():
                    self.root.destroy()
                print("Thank you for using TAR UMT Student Assistant!")
                sys.exit(0)
        except Exception as e:
            print(f"Error during exit: {e}")
            sys.exit(1)


def main():
    """Main application entry point"""
    print("=" * 80)
    print("TAR UMT STUDENT ASSISTANT APPLICATION")
    print("Enhanced Student Productivity Suite")
    print("Authors: HO JUN YON and NA THEE LOK")
    print("Course: AMCS1034 Software Development Fundamentals")
    print("=" * 80)

    # Check system requirements
    if not check_requirements():
        print("\nCRITICAL: Missing required dependencies!")
        print("Please install missing packages and try again.")
        return False

    print("\n✅ ALL REQUIREMENTS MET!")
    print("Launching Student Assistant Application...")
    print("=" * 80)

    try:
        # Setup cleanup
        atexit.register(cleanup_application)

        # Launch main application
        app = MainMenuApp()
        return True

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        print("Thank you for using TAR UMT Student Assistant!")
        return False

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        try:
            messagebox.showerror("Critical Error",
                                 f"Application failed to start:\n\n{str(e)}")
        except:
            pass
        return False

    finally:
        cleanup_application()
        print("\nApplication cleanup complete.")


if __name__ == "__main__":
    """Application entry point"""
    try:
        print("Starting TAR UMT Student Assistant...")
        success = main()

        if success:
            print("Application completed successfully!")
            sys.exit(0)
        else:
            print("Application encountered errors.")
            sys.exit(1)

    except Exception as e:
        print(f"Fatal error during startup: {e}")
        sys.exit(1)

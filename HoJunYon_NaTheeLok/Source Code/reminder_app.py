# Import necessary standard library modules
import platform  # For getting operating system information
import sys  # For system-specific parameters and functions
import threading  # For multi-threading support
import time  # For time-related functions
import tkinter as tk  # For GUI creation
from datetime import datetime, timedelta, date  # For date and time manipulation
from tkinter import messagebox, ttk  # For dialog boxes and themed widgets
import calendar as cal  # For calendar-related functions

# Try to import winsound for Windows audio notifications
try:
    import winsound  # Windows sound playback library
    WINSOUND_AVAILABLE = True  # Flag indicating winsound is available
except ImportError:
    WINSOUND_AVAILABLE = False  # Flag indicating winsound is not available

# Global configurations for color scheme for the application
COLORS = {
    'primary': '#2563eb',  # Main blue color
    'success': '#16a34a',  # Green for success states
    'danger': '#dc2626',   # Red for danger/error states
    'warning': '#d97706',  # Orange for warnings
    'info': '#0891b2',     # Blue for information
    'dark': '#374151',     # Dark gray for text
    'light': '#f3f4f6',    # Light gray for backgrounds
    'white': '#ffffff',    # Pure white
    'background': '#f8fafc',  # Application background color
    'text': '#1f2937',        # Primary text color
    'text_secondary': '#6b7280',  # Secondary text color
    # FIXED: Added missing calendar colors
    'calendar_header': '#4f46e5',        # Header color for calendar
    'calendar_today': '#fbbf24',         # Highlight color for today's date
    'calendar_selected': '#10b981',      # Color for selected date
    'calendar_has_reminders': '#f59e0b',  # Orange for dates with reminders
    'calendar_has_completed': '#22c55e',  # Green for dates with completed reminders
    # Purple for dates with both pending and completed
    'calendar_has_both': '#8b5cf6',
    'calendar_overdue': '#ef4444'        # Red for overdue reminders
}

# Font configurations for the application
FONTS = {
    'header': ('Segoe UI', 16, 'bold'),      # Main headers
    'subheader': ('Segoe UI', 12, 'bold'),   # Subheaders
    'label': ('Segoe UI', 10),               # Regular labels
    'tiny': ('Segoe UI', 8),                 # Small text
    'calendar': ('Segoe UI', 9),             # Calendar text
    'calendar_header': ('Segoe UI', 11, 'bold')  # Calendar headers
}

# Global list to store all reminders
reminders = []
# Application state dictionary to manage running status
APP_STATE = {'running': True}


def apply_theme_to_window(window):
    """Apply theme to window"""
    window.configure(bg=COLORS['background'])


def center_window(window, width, height):
    """Center window on screen"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    # Adjust for taskbar
    y = max(0, y - 20)
    window.geometry(f"{width}x{height}+{x}+{y}")


class EnhancedButton:
    """Styled Button with hover effects"""

    def __init__(self, parent, text="", command=None, button_type='primary', width=10, height=1):
        # Map button types to colors

        color_map = {
            'primary': COLORS['primary'],
            'success': COLORS['success'],
            'danger': COLORS['danger'],
            'warning': COLORS['warning'],
            'info': COLORS['info'],
            'dark': COLORS['dark']
        }

        self.button = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            # Default to primary color
            bg=color_map.get(button_type, COLORS['primary']),
            fg=COLORS['white'],  # White text
            font=FONTS['label'],
            relief='flat',  # Flat button style
            cursor='hand2'  # Hand cursor on hover
        )

        # Hover effects
        def on_enter(e):
            self.button['bg'] = self.lighten_color(
                color_map.get(button_type, COLORS['primary']))

        def on_leave(e):
            self.button['bg'] = color_map.get(button_type, COLORS['primary'])

        # Bind hover events to the button
        self.button.bind("<Enter>", on_enter)
        self.button.bind("<Leave>", on_leave)

    def pack(self, **kwargs):
        self.button.pack(**kwargs)

    def grid(self, **kwargs):
        self.button.grid(**kwargs)

    def lighten_color(self, hex_color, factor=0.1):
        """Lighten a hex color"""
        hex_color = hex_color.lstrip('#')  # Remove '#' if present
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c + (255-c)*factor)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class CalendarWidget:
    """Custom Calendar Widget for date selection with reminder indicators"""

    def __init__(self, parent, callback=None, current_user="DefaultUser"):

        self.callback = callback  # Callback when a date is selected
        self.current_user = current_user  # Current user context
        self.selected_date = date.today()  # Default selected date is today
        self.display_date = date.today().replace(  # Month view starts at current month
            day=1)  # Start at first of current month

        # Main frame for the calendar
        self.frame = tk.Frame(
            parent, bg=COLORS['white'], relief='raised', bd=2)
        self.create_calendar()

    def get_date_reminder_info(self, check_date):
        """Get reminder information for a specific date"""
        date_str = check_date.strftime("%Y-%m-%d")
        today = date.today()

        # Get reminders for this date and user
        date_reminders = [r for r in reminders
                          if r.get('user') == self.current_user
                          and r.get('date', today.strftime("%Y-%m-%d")) == date_str]

        if not date_reminders:
            return None, 0, 0

        completed = sum(1 for r in date_reminders if r.get('done', False))
        pending = len(date_reminders) - completed

        if check_date < today and pending > 0:
            return 'overdue', pending, completed
        elif pending > 0 and completed > 0:
            return 'both', pending, completed
        elif completed > 0 and pending == 0:
            return 'completed', pending, completed
        elif pending > 0:
            return 'pending', pending, completed
        else:
            return None, pending, completed

    def create_calendar(self):
        """Create the calendar interface with reminder indicators"""
        # Clear existing widgets
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Header with navigation
        header_frame = tk.Frame(self.frame, bg=COLORS['calendar_header'])
        header_frame.pack(fill='x', padx=2, pady=2)

        tk.Button(header_frame, text="◀", command=self.prev_month,
                  bg=COLORS['calendar_header'], fg=COLORS['white'],
                  font=FONTS['calendar'], relief='flat', width=3).pack(side='left')

        month_label = tk.Label(header_frame,
                               text=self.display_date.strftime("%B %Y"),
                               bg=COLORS['calendar_header'], fg=COLORS['white'],
                               font=FONTS['calendar_header'])
        month_label.pack(expand=True)

        tk.Button(header_frame, text="▶", command=self.next_month,
                  bg=COLORS['calendar_header'], fg=COLORS['white'],
                  font=FONTS['calendar'], relief='flat', width=3).pack(side='right')

        # Calendar grid with proper alignment
        calendar_frame = tk.Frame(self.frame, bg=COLORS['white'])
        calendar_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Days of week header
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for col, day in enumerate(days):
            tk.Label(calendar_frame, text=day, bg=COLORS['light'],
                     font=FONTS['tiny'], width=5, height=1,
                     relief='solid', bd=1).grid(row=0, column=col, sticky='nsew')

        # Get calendar data (starts from Monday)
        cal_data = cal.monthcalendar(
            self.display_date.year, self.display_date.month)

        # Create calendar grid
        for week_num, week in enumerate(cal_data):
            for day_col, day_num in enumerate(week):
                row = week_num + 1  # +1 because row 0 is headers

                if day_num == 0:
                    # Empty cell
                    tk.Label(calendar_frame, text="", bg=COLORS['white'],
                             width=5, height=2, relief='solid', bd=1).grid(
                        row=row, column=day_col, sticky='nsew')
                else:
                    day_date = date(self.display_date.year,
                                    self.display_date.month, day_num)

                    # Get reminder info for this date
                    reminder_type, pending_count, completed_count = self.get_date_reminder_info(
                        day_date)

                    # Determine button appearance
                    if day_date == self.selected_date:
                        # Selected date - always use selected color with white text
                        bg_color = COLORS['calendar_selected']
                        fg_color = COLORS['white']
                        button_text = str(day_num)
                    elif day_date == date.today():
                        # Today - use today color but show reminder indicator
                        bg_color = COLORS['calendar_today']
                        fg_color = COLORS['dark']
                        button_text = str(day_num)
                        if reminder_type:
                            button_text += f"\n•"  # Add dot indicator
                    elif reminder_type == 'overdue':
                        bg_color = COLORS['calendar_overdue']
                        fg_color = COLORS['white']
                        button_text = f"{day_num}\n{pending_count}!"
                    elif reminder_type == 'both':
                        bg_color = COLORS['calendar_has_both']
                        fg_color = COLORS['white']
                        button_text = f"{day_num}\n{pending_count}+{completed_count}"
                    elif reminder_type == 'completed':
                        bg_color = COLORS['calendar_has_completed']
                        fg_color = COLORS['white']
                        button_text = f"{day_num}\n✓{completed_count}"
                    elif reminder_type == 'pending':
                        bg_color = COLORS['calendar_has_reminders']
                        fg_color = COLORS['white']
                        button_text = f"{day_num}\n{pending_count}"
                    else:
                        # No reminders
                        bg_color = COLORS['white']
                        fg_color = COLORS['text']
                        button_text = str(day_num)

                    btn = tk.Button(calendar_frame, text=button_text,
                                    bg=bg_color, fg=fg_color,
                                    font=FONTS['calendar'], width=5, height=2,
                                    relief='solid', bd=1,
                                    command=lambda d=day_date: self.select_date(d))
                    btn.grid(row=row, column=day_col, sticky='nsew')

        # Configure grid weights for proper resizing
        for i in range(7):  # 7 columns
            calendar_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(cal_data) + 1):  # +1 for header row
            calendar_frame.grid_rowconfigure(i, weight=1)

        # Selected date display and legend
        info_frame = tk.Frame(self.frame, bg=COLORS['light'])
        info_frame.pack(fill='x', padx=5, pady=5)

        # Selected date
        selected_frame = tk.Frame(info_frame, bg=COLORS['light'])
        selected_frame.pack(fill='x', pady=(0, 5))

        tk.Label(selected_frame, text="Selected Date:",
                 font=FONTS['tiny'], bg=COLORS['light']).pack(side='left')
        tk.Label(selected_frame, text=self.selected_date.strftime("%Y-%m-%d"),
                 font=FONTS['label'], bg=COLORS['light'],
                 fg=COLORS['success']).pack(side='right')

        # Legend
        legend_frame = tk.Frame(info_frame, bg=COLORS['light'])
        legend_frame.pack(fill='x')

        tk.Label(legend_frame, text="Legend:",
                 font=FONTS['tiny'], bg=COLORS['light'], fg=COLORS['text']).pack(anchor='w')

        legend_items = [
            ("● Today", COLORS['calendar_today']),
            ("● Has Reminders", COLORS['calendar_has_reminders']),
            ("● Completed", COLORS['calendar_has_completed']),
            ("● Mixed", COLORS['calendar_has_both']),
            ("● Overdue", COLORS['calendar_overdue'])
        ]

        for i, (text, color) in enumerate(legend_items):
            if i < 3:  # First row
                row_frame = legend_frame if i == 0 else row_frame
                if i == 0:
                    row_frame = tk.Frame(legend_frame, bg=COLORS['light'])
                    row_frame.pack(fill='x')
            else:  # Second row
                if i == 3:
                    row_frame = tk.Frame(legend_frame, bg=COLORS['light'])
                    row_frame.pack(fill='x')

            item_frame = tk.Frame(row_frame, bg=COLORS['light'])
            item_frame.pack(side='left', padx=5)

            color_label = tk.Label(item_frame, text="■ ", fg=color,
                                   bg=COLORS['light'], font=FONTS['tiny'])
            color_label.pack(side='left')

            tk.Label(item_frame, text=text.replace("● ", ""),
                     font=FONTS['tiny'], bg=COLORS['light']).pack(side='left')

    def prev_month(self):
        """Go to previous month"""
        if self.display_date.month == 1:
            self.display_date = self.display_date.replace(
                year=self.display_date.year-1, month=12)
        else:
            self.display_date = self.display_date.replace(
                month=self.display_date.month-1)
        self.create_calendar()

    def next_month(self):
        """Go to next month"""
        if self.display_date.month == 12:
            self.display_date = self.display_date.replace(
                year=self.display_date.year+1, month=1)
        else:
            self.display_date = self.display_date.replace(
                month=self.display_date.month+1)
        self.create_calendar()

    def select_date(self, selected_date):
        """Select a date"""
        self.selected_date = selected_date
        self.create_calendar()
        if self.callback:
            self.callback(selected_date)

    def get_selected_date(self):
        """Get the currently selected date"""
        return self.selected_date

    def refresh_calendar(self):
        """Refresh calendar to update reminder indicators"""
        self.create_calendar()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)


class ReminderApp:
    """Enhanced Reminder Application with Calendar"""

    def __init__(self, current_user=None, return_callback=None):
        self.return_callback = return_callback  # Callback to return to main menu
        self.current_user = current_user or "DefaultUser"  # Current user context
        self.current_window = None  # Main window
        self.clock_label = None  # Label to display current time
        self.reminder_listbox = None  # Listbox to display reminders
        self.reminder_entry = None  # Entry for reminder message
        self.time_entry = None  # Entry for reminder time
        self.category_entry = None  # Entry for reminder category
        self.search_entry = None  # Entry for search
        self.calendar_widget = None  # Calendar widget
        self.date_entry = None  # Entry for reminder date
        self.calendar_window = None  # Calendar popup window

        self.reminder_lock = threading.Lock()  # Lock for thread-safe reminder access
        self.clock_running = True  # Flag to control clock thread

        print(f"Starting Enhanced Reminder App for user: {self.current_user}")
        self.show_reminder_interface()  # Start the main interface

    def show_reminder_interface(self):
        """Main Reminder App interface"""
        try:
            # Create main window
            self.current_window = tk.Tk()
            self.current_window.title(
                f"📅 Smart Reminder Assistant - {self.current_user}")
            apply_theme_to_window(self.current_window)
            self.current_window.resizable(True, True)
            self.current_window.minsize(1000, 700)
            screen_width = self.current_window.winfo_screenwidth()
            screen_height = self.current_window.winfo_screenheight()
            window_width = min(1600, int(screen_width * 0.75))
            window_height = min(1000, int(screen_height * 0.8))
            center_window(self.current_window, window_width, window_height)

            main_frame = tk.Frame(self.current_window, bg=COLORS['background'],
                                  padx=30, pady=25)
            main_frame.pack(expand=True, fill='both')

            # Header
            header_frame = tk.Frame(main_frame, bg=COLORS['background'])
            header_frame.pack(fill='x', pady=(0, 25))

            user_frame = tk.Frame(header_frame, bg=COLORS['background'])
            user_frame.pack(fill='x', pady=(0, 10))

            title_label = tk.Label(user_frame, text="📅 Smart Reminder Assistant",
                                   font=("Segoe UI", 22, "bold"),
                                   fg=COLORS['primary'], bg=COLORS['background'])
            title_label.pack(side='left')

            controls_frame = tk.Frame(user_frame, bg=COLORS['background'])
            controls_frame.pack(side='right')

            EnhancedButton(controls_frame, text="📅 Calendar View",
                           command=self.show_calendar_view, button_type='info',
                           width=15, height=1).pack(side='right', padx=5)
            EnhancedButton(controls_frame, text="← Back to Main Menu",
                           command=self.back_to_main_menu, button_type='dark',
                           width=18, height=1).pack(side='right', padx=5)

            welcome_label = tk.Label(header_frame, text=f"Welcome, {self.current_user}!",
                                     font=("Segoe UI", 14),
                                     fg=COLORS['success'], bg=COLORS['background'])
            welcome_label.pack(pady=5)

            # Clock
            clock_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                   bd=2, padx=20, pady=15)
            clock_frame.pack(fill='x', pady=10)
            tk.Label(clock_frame, text="🕐 Current Time", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack()
            self.clock_label = tk.Label(clock_frame, font=("Segoe UI", 18, "bold"),
                                        fg=COLORS['success'], bg=COLORS['white'])
            self.clock_label.pack(pady=5)

            # Input section
            input_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='raised',
                                   bd=2, padx=30, pady=25)
            input_frame.pack(fill='x', pady=15)
            tk.Label(input_frame, text="➕ Create New Reminder", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=(0, 15))
            input_grid = tk.Frame(input_frame, bg=COLORS['white'])
            input_grid.pack(fill='x')

            # Reminder message
            tk.Label(input_grid, text="*  Reminder Message:", bg=COLORS['white'],
                     fg=COLORS['text'], font=FONTS['label']).grid(row=0, column=0,
                                                                  padx=5, pady=8, sticky='w')
            self.reminder_entry = tk.Entry(input_grid, font=FONTS['label'], width=35,
                                           relief='solid', bd=1, bg=COLORS['light'])
            self.reminder_entry.grid(
                row=0, column=1, padx=10, pady=8, sticky='ew')

            # Date selection
            tk.Label(input_grid, text="*  Date (YYYY-MM-DD):", bg=COLORS['white'],
                     fg=COLORS['text'], font=FONTS['label']).grid(row=1, column=0,
                                                                  padx=5, pady=8, sticky='w')
            date_frame = tk.Frame(input_grid, bg=COLORS['white'])
            date_frame.grid(row=1, column=1, padx=10, pady=8, sticky='w')

            self.date_entry = tk.Entry(date_frame, font=FONTS['label'], width=15,
                                       relief='solid', bd=1, bg=COLORS['light'])
            self.date_entry.pack(side='left')
            self.date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

            EnhancedButton(date_frame, text="📅 Pick Date",
                           command=self.open_date_picker, button_type='info',
                           width=10, height=1).pack(side='left', padx=5)

            # Time selection
            tk.Label(input_grid, text="*  Time (HH:MM:SS):", bg=COLORS['white'],
                     fg=COLORS['text'], font=FONTS['label']).grid(row=2, column=0,
                                                                  padx=5, pady=8, sticky='w')
            self.time_entry = tk.Entry(input_grid, font=FONTS['label'], width=20,
                                       relief='solid', bd=1, bg=COLORS['light'])
            self.time_entry.grid(row=2, column=1, padx=10, pady=8, sticky='w')

            # Category
            tk.Label(input_grid, text="*  Category:", bg=COLORS['white'],
                     fg=COLORS['text'], font=FONTS['label']).grid(row=3, column=0,
                                                                  padx=5, pady=8, sticky='w')
            self.category_entry = tk.Entry(input_grid, font=FONTS['label'], width=25,
                                           relief='solid', bd=1, bg=COLORS['light'])
            self.category_entry.grid(
                row=3, column=1, padx=10, pady=8, sticky='w')

            input_grid.grid_columnconfigure(1, weight=1)

            EnhancedButton(input_frame, text="➕ Add Reminder",
                           command=self.add_reminder, button_type='success',
                           width=20, height=2).pack(pady=15)

            # Search section
            search_frame = tk.Frame(main_frame, bg=COLORS['light'], relief='raised',
                                    bd=1, padx=20, pady=15)
            search_frame.pack(fill='x', pady=10)
            search_controls = tk.Frame(search_frame, bg=COLORS['light'])
            search_controls.pack(fill='x')

            tk.Label(search_controls, text="🔍 Search (Only) Category/Message:", bg=COLORS['light'],
                     fg=COLORS['text'], font=FONTS['label']).pack(side='left', padx=5)
            self.search_entry = tk.Entry(search_controls, font=FONTS['label'], width=30,
                                         relief='solid', bd=1, bg=COLORS['white'])
            self.search_entry.pack(side='left', padx=10)
            EnhancedButton(search_controls, text="🔍 Search",
                           command=self.search_reminders, button_type='info',
                           width=10, height=1).pack(side='left', padx=5)
            EnhancedButton(search_controls, text="📋 Show All",
                           command=self.show_all_reminders, button_type='primary',
                           width=10, height=1).pack(side='left', padx=5)
            EnhancedButton(search_controls, text="📅 Today  ",
                           command=self.show_todays_reminders, button_type='warning',
                           width=15, height=1).pack(side='left', padx=5)
            EnhancedButton(search_controls, text="📅 Choose by Date",
                           command=self.filter_by_date, button_type='info',
                           width=15, height=1).pack(side='left', padx=5)

            # Reminder list
            list_frame = tk.Frame(
                main_frame, bg=COLORS['white'], relief='raised', bd=2)
            list_frame.pack(fill='both', expand=True, pady=15)
            tk.Label(list_frame, text="📝 Your Reminders", font=FONTS['subheader'],
                     bg=COLORS['white'], fg=COLORS['text']).pack(pady=15)
            listbox_frame = tk.Frame(list_frame, bg=COLORS['white'])
            listbox_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
            self.reminder_listbox = tk.Listbox(listbox_frame, font=FONTS['label'],
                                               height=10, bg=COLORS['light'],
                                               fg=COLORS['text'], relief='solid', bd=1)
            scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL,
                                     command=self.reminder_listbox.yview)
            self.reminder_listbox.configure(yscrollcommand=scrollbar.set)
            self.reminder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Action buttons
            btn_frame = tk.Frame(main_frame, bg=COLORS['background'])
            btn_frame.pack(pady=20)
            EnhancedButton(btn_frame, text="✅ Mark Done",
                           command=self.mark_reminder_done, button_type='success',
                           width=14, height=2).pack(side='left', padx=8)
            EnhancedButton(btn_frame, text="🗑 Delete",
                           command=self.delete_selected_reminder, button_type='danger',
                           width=14, height=2).pack(side='left', padx=8)
            EnhancedButton(btn_frame, text="🧹 Clear All",
                           command=self.clear_all_reminders, button_type='warning',
                           width=14, height=2).pack(side='left', padx=8)

            # Init
            self.update_reminder_listbox()
            self.start_reminder_checker()
            self.update_reminder_clock()

            # Key bindings
            self.reminder_entry.bind('<Return>', lambda e: self.add_reminder())
            self.time_entry.bind('<Return>', lambda e: self.add_reminder())
            self.category_entry.bind('<Return>', lambda e: self.add_reminder())
            self.date_entry.bind('<Return>', lambda e: self.add_reminder())
            self.search_entry.bind(
                '<Return>', lambda e: self.search_reminders())

            self.current_window.protocol(
                "WM_DELETE_WINDOW", self.back_to_main_menu)
            self.current_window.mainloop()

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to create reminder app: {str(e)}")

    def open_date_picker(self):
        """Open date picker window"""
        # If already open, bring to front
        if self.calendar_window and self.calendar_window.winfo_exists():
            self.calendar_window.lift()
            return

        self.calendar_window = tk.Toplevel(self.current_window)
        self.calendar_window.title("📅 Select Date")
        apply_theme_to_window(self.calendar_window)
        center_window(self.calendar_window, 450, 550)
        self.calendar_window.resizable(False, False)

        # Calendar widget with current user context
        self.calendar_widget = CalendarWidget(self.calendar_window,
                                              callback=self.on_date_selected,
                                              current_user=self.current_user)
        self.calendar_widget.pack(padx=10, pady=10, fill='both', expand=True)

        # Buttons
        btn_frame = tk.Frame(self.calendar_window, bg=COLORS['background'])
        btn_frame.pack(fill='x', padx=10, pady=10)

        EnhancedButton(btn_frame, text="✅ Select",
                       command=self.confirm_date_selection, button_type='success',
                       width=12, height=1).pack(side='right', padx=5)
        EnhancedButton(btn_frame, text="❌ Cancel",
                       command=self.calendar_window.destroy, button_type='danger',
                       width=12, height=1).pack(side='right', padx=5)

    def on_date_selected(self, selected_date):
        """Handle date selection from calendar"""
        pass  # Just for visual feedback

    def confirm_date_selection(self):
        """Confirm date selection and update entry"""
        if self.calendar_widget:
            selected_date = self.calendar_widget.get_selected_date()
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, selected_date.strftime("%Y-%m-%d"))
            self.calendar_window.destroy()

    def show_calendar_view(self):
        """Show calendar view with reminders in table format"""
        calendar_view = tk.Toplevel(self.current_window)
        calendar_view.title("📅 Calendar View - Your Reminders")
        apply_theme_to_window(calendar_view)
        center_window(calendar_view, 1200, 800)

        main_frame = tk.Frame(
            calendar_view, bg=COLORS['background'], padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # Header
        header_frame = tk.Frame(main_frame, bg=COLORS['background'])
        header_frame.pack(fill='x', pady=(0, 20))

        tk.Label(header_frame, text="📅 Calendar View", font=FONTS['header'],
                 bg=COLORS['background'], fg=COLORS['primary']).pack(pady=(0, 10))

        # Calendar widget with current user context
        cal_widget = CalendarWidget(main_frame, callback=self.show_date_reminders,
                                    current_user=self.current_user)
        cal_widget.pack(side='top', fill='x', pady=(0, 20))

        # Reminders for selected date in table format
        table_frame = tk.Frame(
            main_frame, bg=COLORS['white'], relief='raised', bd=2)
        table_frame.pack(fill='both', expand=True)

        # Create Treeview for table display
        columns = ("category", "date", "time", "message", "status")
        self.date_reminders_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=8)

        # Define headings
        self.date_reminders_tree.heading("category", text="Category")
        self.date_reminders_tree.heading("date", text="Date")
        self.date_reminders_tree.heading("time", text="Time")
        self.date_reminders_tree.heading("message", text="Message")
        self.date_reminders_tree.heading("status", text="Status")

        # Set column widths
        self.date_reminders_tree.column("category", width=100, anchor="center")
        self.date_reminders_tree.column("date", width=100, anchor="center")
        self.date_reminders_tree.column("time", width=80, anchor="center")
        self.date_reminders_tree.column("message", width=300, anchor="w")
        self.date_reminders_tree.column("status", width=80, anchor="center")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.date_reminders_tree.yview)
        self.date_reminders_tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.date_reminders_tree.pack(
            side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        # Label to show selected date
        self.date_reminders_label = tk.Label(table_frame, text="Select a date to view reminders",
                                             font=FONTS['subheader'], bg=COLORS['white'],
                                             fg=COLORS['text'])
        self.date_reminders_label.pack(pady=5)

        # Show today's reminders initially
        today = date.today()
        self.show_date_reminders(today)
        self.date_reminders_label.config(
            text=f"Reminders for {today.strftime('%Y-%m-%d')}")

    def show_date_reminders(self, selected_date):
        """Show reminders for a specific date in table format"""
        if hasattr(self, 'date_reminders_tree'):
            # Clear existing items
            for item in self.date_reminders_tree.get_children():
                self.date_reminders_tree.delete(item)

            self.date_reminders_label.config(
                text=f"Reminders for {selected_date.strftime('%Y-%m-%d')}")

            date_str = selected_date.strftime("%Y-%m-%d")
            with self.reminder_lock:
                date_reminders = [r for r in reminders
                                  if r.get('user') == self.current_user
                                  and r.get('date', date.today().strftime("%Y-%m-%d")) == date_str]

            if not date_reminders:
                # Add a placeholder row
                self.date_reminders_tree.insert("", "end", values=(
                    "No reminders", "", "", "for this date", ""))
                return

            for r in date_reminders:
                status = "✅" if r["done"] else (
                    "📢" if r.get("notified") else "⏰")
                category = r.get('category', 'General')
                reminder_date = r.get(
                    'date', date.today().strftime("%Y-%m-%d"))

                self.date_reminders_tree.insert("", "end", values=(
                    category,
                    reminder_date,
                    r['time'],
                    r['text'],
                    status
                ))

    def filter_by_date(self):
        """Open date picker to filter reminders by selected date"""
        filter_window = tk.Toplevel(self.current_window)
        filter_window.title("📅 Filter Reminders by Date")
        apply_theme_to_window(filter_window)
        center_window(filter_window, 450, 600)
        filter_window.resizable(False, False)

        # Instructions
        tk.Label(filter_window, text="Select a date to view reminders:",
                 font=FONTS['subheader'], bg=COLORS['background'],
                 fg=COLORS['text']).pack(pady=10)

        # Calendar widget for filtering with current user context (allow past dates for viewing)
        filter_calendar = CalendarWidget(
            filter_window, current_user=self.current_user)
        filter_calendar.pack(padx=10, pady=10, fill='both', expand=True)

        # Buttons
        btn_frame = tk.Frame(filter_window, bg=COLORS['background'])
        btn_frame.pack(fill='x', padx=10, pady=10)

        def apply_date_filter():
            selected_date = filter_calendar.get_selected_date()
            date_str = selected_date.strftime("%Y-%m-%d")

            with self.reminder_lock:
                date_reminders = [r for r in reminders
                                  if r.get('user') == self.current_user
                                  and r.get('date', date.today().strftime("%Y-%m-%d")) == date_str]

            self.update_reminder_listbox(date_reminders)

            # Update search entry to show current filter
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, f"Date: {date_str}")

            messagebox.showinfo("Date Filter Applied",
                                f"📅 Showing {len(date_reminders)} reminder(s) for {date_str}")
            filter_window.destroy()

        EnhancedButton(btn_frame, text="✅ Apply Filter",
                       command=apply_date_filter, button_type='success',
                       width=12, height=1).pack(side='right', padx=5)
        EnhancedButton(btn_frame, text="❌ Cancel",
                       command=filter_window.destroy, button_type='danger',
                       width=12, height=1).pack(side='right', padx=5)

    def show_todays_reminders(self):
        """Filter and show today's reminders"""
        today_str = date.today().strftime("%Y-%m-%d")
        with self.reminder_lock:
            today_reminders = [r for r in reminders
                               if r.get('user') == self.current_user
                               and r.get('date', today_str) == today_str]

        self.update_reminder_listbox(today_reminders)

        # Update search entry to show current filter
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, f"Today: {today_str}")

        messagebox.showinfo(
            "Today's Reminders", f"📅 Showing {len(today_reminders)} reminder(s) for today")

    def add_reminder(self):
        """Add a new reminder with date support and past date/time validation"""
        try:
            text = self.reminder_entry.get().strip()
            reminder_time = self.time_entry.get().strip()
            reminder_date = self.date_entry.get().strip()
            category = self.category_entry.get().strip()

            if not text or not reminder_time or not reminder_date:
                messagebox.showwarning(
                    "Warning", "Reminder message, date, and time are all required!")
                return

            try:
                # Validate date format
                parsed_date = datetime.strptime(
                    reminder_date, "%Y-%m-%d").date()
                # Validate time format
                parsed_time = datetime.strptime(
                    reminder_time, "%H:%M:%S").time()

                # Get current date and time
                current_datetime = datetime.now()
                current_date = current_datetime.date()
                current_time = current_datetime.time()

                # Create the full reminder datetime for comparison
                reminder_datetime = datetime.combine(parsed_date, parsed_time)

                # Validation 1: Check if date is in the past
                if parsed_date < current_date:
                    messagebox.showerror("Invalid Date",
                                         f"❌ Cannot create reminder for past date!\n\n"
                                         f"Selected date: {reminder_date}\n"
                                         f"Current date: {current_date.strftime('%Y-%m-%d')}\n\n"
                                         f"Please select today's date or a future date.")
                    return

                # Validation 2: Check if it's today but time is in the past
                elif parsed_date == current_date and parsed_time <= current_time:
                    # Add a small buffer (1 minute) to allow for immediate reminders
                    buffer_time = (current_datetime +
                                   timedelta(minutes=1)).time()
                    messagebox.showerror("Invalid Time",
                                         f"❌ Cannot create reminder for past time!\n\n"
                                         f"Selected time: {reminder_time}\n"
                                         f"Current time: {current_time.strftime('%H:%M:%S')}\n\n"
                                         f"For today's date, please set time to at least {buffer_time.strftime('%H:%M:%S')} or later.")
                    return

                # Validation 3: Check if the reminder datetime is too far in the future (optional - prevents accidental entries)
                max_future_date = current_date + \
                    timedelta(days=365 * 2)  # 2 years from now
                if parsed_date > max_future_date:
                    result = messagebox.askyesno("Far Future Date",
                                                 f"⚠ Warning: The selected date is more than 2 years in the future.\n\n"
                                                 f"Selected date: {reminder_date}\n"
                                                 f"That's {(parsed_date - current_date).days} days from now.\n\n"
                                                 f"Are you sure you want to create this reminder?")
                    if not result:
                        return

                # All validations passed - create the reminder
                with self.reminder_lock:
                    reminders.append({
                        "text": text,
                        "time": reminder_time,
                        "date": reminder_date,
                        "category": category if category else "General",
                        "done": False,
                        "notified": False,
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "user": self.current_user
                    })

                self.update_reminder_listbox()  # Refresh listbox
                self.reminder_entry.delete(0, tk.END)  # Clear message entry
                self.time_entry.delete(0, tk.END)  # Clear time entry
                self.category_entry.delete(0, tk.END)  # Clear category entry
                # Keep date for next reminder

                # Refresh any open calendar widgets to show the new reminder
                if hasattr(self, 'calendar_widget') and self.calendar_widget:
                    try:
                        self.calendar_widget.refresh_calendar()
                    except:
                        pass

                # Show success message with time until reminder
                time_until = reminder_datetime - current_datetime
                if time_until.days > 0:
                    time_desc = f"in {time_until.days} day(s)"
                elif time_until.seconds > 3600:
                    hours = time_until.seconds // 3600
                    minutes = (time_until.seconds % 3600) // 60
                    time_desc = f"in {hours} hour(s) and {minutes} minute(s)"
                elif time_until.seconds > 60:
                    minutes = time_until.seconds // 60
                    time_desc = f"in {minutes} minute(s)"
                else:
                    time_desc = "very soon"

                messagebox.showinfo("Success", f"✅ Reminder added successfully!\n\n"
                                    f"📝 Message: {text}\n"
                                    f"📅 Date: {reminder_date}\n"
                                    f"⏰ Time: {reminder_time}\n"
                                    f"📂 Category: {category if category else 'General'}\n"
                                    f"⏳ Reminder will trigger {time_desc}")

            except ValueError as ve:
                if "time" in str(ve).lower():
                    messagebox.showerror("Error",
                                         "❌ Invalid time format!\n\n"
                                         "Time must be in HH:MM:SS format\n"
                                         "Examples:\n"
                                         "• 14:30:00 (2:30 PM)\n"
                                         "• 09:15:30 (9:15:30 AM)\n"
                                         "• 23:45:00 (11:45 PM)")
                else:
                    messagebox.showerror("Error",
                                         "❌ Invalid date format!\n\n"
                                         "Date must be in YYYY-MM-DD format\n"
                                         "Examples:\n"
                                         "• 2024-12-25\n"
                                         "• 2024-01-01\n"
                                         "• 2025-03-15")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add reminder: {str(e)}")

    def update_reminder_listbox(self, filtered=None):
        """Refresh reminder listbox with date information"""
        try:
            self.reminder_listbox.delete(0, tk.END)
            with self.reminder_lock:
                items = filtered if filtered is not None else reminders.copy()

            user_reminders = [r for r in items if r.get(
                'user') == self.current_user]
            if not user_reminders:
                self.reminder_listbox.insert(
                    tk.END, "🔭 No reminders yet. Add your first reminder above!")
                return

            # Sort reminders by date and time
            user_reminders.sort(key=lambda x: (
                x.get('date', date.today().strftime("%Y-%m-%d")),
                x['time']
            ))

            for r in user_reminders:
                category_text = f"[{r['category']}] " if r.get(
                    'category') else ""
                date_text = r.get('date', date.today().strftime("%Y-%m-%d"))
                status_text = " ✅ [COMPLETED]" if r["done"] else (
                    " 📢 [NOTIFIED]" if r.get("notified", False) else "")
                display_text = f"{category_text}{r['text']} - {date_text} at {r['time']}{status_text}"
                self.reminder_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error updating listbox: {e}")

    def search_reminders(self):
        """Search reminders including date"""
        try:
            keyword = self.search_entry.get().strip().lower()
            if not keyword:
                self.update_reminder_listbox()
                return

            with self.reminder_lock:
                user_reminders = [r for r in reminders if r.get(
                    'user') == self.current_user]
                filtered = [r for r in user_reminders if
                            keyword in r["text"].lower() or
                            keyword in r.get("category", "").lower() or
                            keyword in r["time"] or
                            keyword in r.get("date", "")]

            self.update_reminder_listbox(filtered)
            if not filtered:
                messagebox.showinfo(
                    "Search Results", f"🔍 No reminders found matching '{keyword}'")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to search reminders: {str(e)}")

    def show_all_reminders(self):
        """Show all reminders"""
        try:
            self.search_entry.delete(0, tk.END)
            self.update_reminder_listbox()
            with self.reminder_lock:
                user_reminders = [r for r in reminders if r.get(
                    'user') == self.current_user]
            messagebox.showinfo(
                "All Reminders", f"📋 Showing all {len(user_reminders)} reminder(s)")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to show all reminders: {str(e)}")

    def mark_reminder_done(self):
        """Mark selected reminder as done"""
        try:
            selected = self.reminder_listbox.curselection()
            if not selected:
                messagebox.showinfo(
                    "Info", "Please select a reminder to mark as done.")
                return
            selected_text = self.reminder_listbox.get(selected[0])
            with self.reminder_lock:
                for r in reminders:
                    if (r['user'] == self.current_user
                        and r['text'] in selected_text
                        and r['time'] in selected_text
                            and r.get('date', date.today().strftime("%Y-%m-%d")) in selected_text):
                        r["done"] = True
                        break
            self.update_reminder_listbox()

            # Refresh any open calendar widgets to update colors
            if hasattr(self, 'calendar_widget') and self.calendar_widget:
                try:
                    self.calendar_widget.refresh_calendar()
                except:
                    pass

            messagebox.showinfo("Success", "✅ Reminder marked as completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark reminder: {str(e)}")

    def delete_selected_reminder(self):
        """Delete selected reminder"""
        try:
            selected = self.reminder_listbox.curselection()
            if not selected:
                messagebox.showinfo(
                    "Info", "Please select a reminder to delete.")
                return
            selected_text = self.reminder_listbox.get(selected[0])
            with self.reminder_lock:
                for r in reminders:
                    if (r['user'] == self.current_user
                        and r['text'] in selected_text
                        and r['time'] in selected_text
                            and r.get('date', date.today().strftime("%Y-%m-%d")) in selected_text):
                        result = messagebox.askyesno("Confirm Deletion",
                                                     f"Are you sure you want to delete this reminder?\n\n"
                                                     f"📝 {r['text']}\n"
                                                     f"📅 {r.get('date', 'Today')}\n"
                                                     f"⏰ {r['time']}\n"
                                                     f"📂 {r.get('category', 'General')}")
                        if result:
                            reminders.remove(r)
                            break
            self.update_reminder_listbox()

            # Refresh any open calendar widgets to update colors
            if hasattr(self, 'calendar_widget') and self.calendar_widget:
                try:
                    self.calendar_widget.refresh_calendar()
                except:
                    pass

            messagebox.showinfo("Success", "🗑 Reminder deleted successfully!")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to delete reminder: {str(e)}")

    def clear_all_reminders(self):
        """Clear all reminders for current user"""
        try:
            with self.reminder_lock:
                user_reminders = [r for r in reminders if r.get(
                    'user') == self.current_user]

            if not user_reminders:
                messagebox.showinfo("Info", "No reminders to clear.")
                return

            result = messagebox.askyesno(
                "Confirm Clear All",
                f"Are you sure you want to clear all your reminders?\n\n"
                f"This will delete {len(user_reminders)} reminder(s).\n"
                f"This action cannot be undone!"
            )
            if result:
                with self.reminder_lock:
                    reminders[:] = [r for r in reminders if r.get(
                        'user') != self.current_user]
                self.update_reminder_listbox()

                # Refresh any open calendar widgets to update colors
                if hasattr(self, 'calendar_widget') and self.calendar_widget:
                    try:
                        self.calendar_widget.refresh_calendar()
                    except:
                        pass

                messagebox.showinfo("Success", "🧹 All your reminders cleared!")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to clear reminders: {str(e)}")

    def update_reminder_clock(self):
        """Update the live clock label every second"""
        try:
            if (self.clock_running and
                hasattr(self, 'clock_label') and
                self.clock_label and
                self.clock_label.winfo_exists() and
                self.current_window and
                    self.current_window.winfo_exists()):

                now = datetime.now()
                time_str = now.strftime("%H:%M:%S")
                date_str = now.strftime("%A, %B %d, %Y")
                self.clock_label.config(text=f"{time_str}\n{date_str}")
                self.current_window.after(1000, self.update_reminder_clock)
        except tk.TclError:
            self.clock_running = False
        except Exception as e:
            print(f"Clock update error: {e}")

    def start_reminder_checker(self):
        """Background thread that checks reminders and notifies at the right time"""
        def check_reminders():
            while APP_STATE['running'] and self.clock_running:
                try:
                    now = datetime.now()
                    current_date = now.strftime("%Y-%m-%d")
                    current_time = now.strftime("%H:%M:%S")

                    # Consider a 3-second window to avoid missing ticks
                    time_window = [(now - timedelta(seconds=i)
                                    ).strftime("%H:%M:%S") for i in range(3)]

                    with self.reminder_lock:
                        user_reminders = [r for r in reminders if r.get(
                            'user') == self.current_user]
                        to_notify = []
                        for r in user_reminders:
                            reminder_date = r.get('date', current_date)
                            if (reminder_date == current_date and
                                r["time"] in time_window and
                                not r["done"] and
                                    not r.get("notified", False)):
                                r["notified"] = True
                                to_notify.append(r)

                    for r in to_notify:
                        if self.current_window and self.current_window.winfo_exists():
                            # Show popup from GUI thread
                            self.current_window.after(
                                0,
                                lambda rr=r: messagebox.showinfo(
                                    "📢 Reminder Alert!",
                                    f"⏰ It's time!\n\n"
                                    f"📝 {rr['text']}\n"
                                    f"📅 Date: {rr.get('date', 'Today')}\n"
                                    f"⏰ Time: {rr['time']}\n"
                                    f"📂 Category: {rr.get('category', 'General')}\n"
                                    f"👤 User: {rr.get('user', 'Unknown')}"
                                )
                            )
                            self.play_reminder_sound()
                            self.current_window.after(
                                0, self.update_reminder_listbox)

                            # Refresh any open calendar widgets to update colors
                            if hasattr(self, 'calendar_widget') and self.calendar_widget:
                                try:
                                    self.current_window.after(
                                        0, lambda: self.calendar_widget.refresh_calendar())
                                except:
                                    pass

                    time.sleep(1)
                except Exception as e:
                    print(f"Error in reminder checker: {e}")
                    time.sleep(1)

        threading.Thread(target=check_reminders, daemon=True).start()

    def play_reminder_sound(self):
        """Play reminder sound without blocking the UI"""
        def _beep():
            try:
                if platform.system() == "Windows" and WINSOUND_AVAILABLE:
                    for _ in range(3):
                        winsound.Beep(1000, 300)
                        time.sleep(0.1)
                else:
                    for _ in range(3):
                        print('\a')
                        time.sleep(0.1)
            except Exception as e:
                print(f"Could not play sound: {e}")
                print('\a')

        threading.Thread(target=_beep, daemon=True).start()

    def back_to_main_menu(self):
        """Handle window close / back with proper cleanup"""
        try:
            result = messagebox.askyesno(
                "Return to Main Menu",
                "Return to main menu?\n\nYour reminders will continue running in the background."
            )
            if result:
                self.clock_running = False
                if self.current_window and self.current_window.winfo_exists():
                    self.current_window.destroy()

                if self.return_callback:
                    # Keep APP_STATE running when returning to a parent menu
                    self.return_callback()
                else:
                    # If no callback, we're quitting the app entirely
                    APP_STATE['running'] = False
                    print("Exiting application...")
                    sys.exit(0)
        except Exception as e:
            print(f"Error returning to main menu: {str(e)}")
            self.clock_running = False
            if self.current_window:
                try:
                    self.current_window.destroy()
                except:
                    pass

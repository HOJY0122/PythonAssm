"""
Fixed Shared UI Components Module
Contains custom UI elements used by both Pomodoro and Reminder apps
"""

import tkinter as tk
from tkinter import messagebox

from shared.config import COLORS, FONTS


class EnhancedButton(tk.Button):
    """Enhanced button with beautiful styling and hover effects"""

    def __init__(self, parent, **kwargs):
        self.button_type = kwargs.pop('button_type', 'primary')
        self.safe_command = kwargs.pop('command', None)

        # Set colors based on button type
        color_map = {
            'primary': COLORS['primary'],
            'success': COLORS['success'],
            'danger': COLORS['danger'],
            'warning': COLORS['warning'],
            'info': COLORS['info'],
            'dark': COLORS['dark']
        }

        self.base_color = color_map.get(self.button_type, COLORS['primary'])
        kwargs['command'] = self._safe_command

        super().__init__(parent, **kwargs)

        self.config(
            bg=self.base_color,
            fg=COLORS['white'],
            relief='flat',
            bd=0,
            cursor='hand2',
            font=FONTS['button'],
            padx=15,
            pady=8,
            activebackground=self._darken_color(self.base_color),
            activeforeground=COLORS['white']
        )

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)

    def _safe_command(self):
        """Safely execute command with error handling"""
        if self.safe_command:
            try:
                self.safe_command()
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def _on_enter(self, event):
        """Handle mouse enter event"""
        try:
            if self.winfo_exists() and self['state'] != 'disabled':
                darker_color = self._darken_color(self.base_color)
                self.config(bg=darker_color)
        except:
            pass

    def _on_leave(self, event):
        """Handle mouse leave event"""
        try:
            if self.winfo_exists() and self['state'] != 'disabled':
                self.config(bg=self.base_color)
        except:
            pass

    def _on_click(self, event):
        """Handle mouse click event"""
        try:
            if self.winfo_exists() and self['state'] != 'disabled':
                much_darker = self._darken_color(
                    self._darken_color(self.base_color))
                self.config(bg=much_darker)
        except:
            pass

    def _on_release(self, event):
        """Handle mouse release event"""
        try:
            if self.winfo_exists() and self['state'] != 'disabled':
                self.config(bg=self.base_color)
        except:
            pass

    def _darken_color(self, color):
        """Enhanced color darkening with better contrast"""
        color_variants = {
            COLORS['primary']: '#1e5f85',
            COLORS['success']: '#2d7a52',
            COLORS['danger']: '#c53030',
            COLORS['warning']: '#9c2b00',
            COLORS['info']: '#4a7c3c',
            COLORS['dark']: '#1a1f2e'
        }
        return color_variants.get(color, color)


class AnimatedProgressBar(tk.Canvas):
    """Animated progress bar with smooth transitions"""

    def __init__(self, parent, width=400, height=25, **kwargs):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=COLORS['background'], **kwargs)

        self.width = width
        self.height = height
        self.progress = 0
        self.target_progress = 0

        try:
            # Create background
            self.create_rectangle(2, 2, width-2, height-2,
                                  fill=COLORS['light'], outline=COLORS['border'], width=2)

            # Create progress bar with gradient effect
            self.progress_rect = self.create_rectangle(2, 2, 2, height-2,
                                                       fill=COLORS['primary'], outline='')

            # Add progress text
            self.progress_text = self.create_text(width//2, height//2,
                                                  text="0%", fill=COLORS['text'],
                                                  font=FONTS['small'])
        except:
            pass

    def set_progress(self, value):
        """Set progress bar value with animation"""
        try:
            if not self.winfo_exists():
                return

            self.target_progress = max(0, min(100, float(value or 0)))
            self._animate_progress()
        except:
            pass

    def _animate_progress(self):
        """Animate progress bar transition"""
        try:
            if not self.winfo_exists():
                return

            # Smooth animation
            diff = self.target_progress - self.progress
            if abs(diff) > 0.5:
                self.progress += diff * 0.1

                bar_width = (self.progress / 100) * (self.width - 4)
                self.coords(self.progress_rect, 2, 2, 2 +
                            bar_width, self.height - 2)

                # Update progress text
                self.itemconfig(self.progress_text,
                                text=f"{int(self.progress)}%")

                # Continue animation
                self.after(50, self._animate_progress)
            else:
                self.progress = self.target_progress
                bar_width = (self.progress / 100) * (self.width - 4)
                self.coords(self.progress_rect, 2, 2, 2 +
                            bar_width, self.height - 2)
                self.itemconfig(self.progress_text,
                                text=f"{int(self.progress)}%")
        except:
            pass


class StatusCard(tk.Frame):
    """Beautiful status card for displaying statistics"""

    def __init__(self, parent, title, value, icon="", color=None, **kwargs):
        super().__init__(
            parent, bg=COLORS['white'], relief='raised', bd=1, **kwargs)

        self.color = color or COLORS['primary']

        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)

        # Icon placeholder (if needed)
        if icon:
            icon_label = tk.Label(self, text=icon, font=("Segoe UI", 16),
                                  bg=COLORS['white'], fg=self.color)
            icon_label.grid(row=0, column=0, rowspan=2,
                            padx=10, pady=10, sticky='w')

        # Title
        title_label = tk.Label(self, text=title, font=FONTS['small'],
                               bg=COLORS['white'], fg=COLORS['text_secondary'])
        title_label.grid(row=0, column=1, sticky='ew', padx=(0, 10))

        # Value
        self.value_label = tk.Label(self, text=str(value), font=FONTS['subheader'],
                                    bg=COLORS['white'], fg=COLORS['text'])
        self.value_label.grid(row=1, column=1, sticky='ew',
                              padx=(0, 10), pady=(0, 5))

    def update_value(self, new_value):
        """Update the displayed value"""
        self.value_label.config(text=str(new_value))

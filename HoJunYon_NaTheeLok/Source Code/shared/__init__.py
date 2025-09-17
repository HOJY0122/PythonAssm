from .config import *
from .database import PomodoroDatabase
from .ui_components import AnimatedProgressBar, EnhancedButton, StatusCard

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

"""
Utility modules for Helmet Detection System.
Provides visualization, database management, and notification functionality.
"""

from .visualization import Visualizer
from .database import DatabaseManager
from .notifier import NotificationManager

__all__ = [
    'Visualizer',
    'DatabaseManager',
    'NotificationManager'
]

# Utility version
__version__ = '1.0.0'

# Default utility configurations
UTIL_CONFIG = {
    'visualization': {
        'colors': {
            'red': (0, 0, 255),
            'green': (0, 255, 0),
            'blue': (255, 0, 0)
        },
        'font_scale': 0.5,
        'thickness': 2
    },
    'database': {
        'pool_size': 5,
        'timeout': 30,
        'retry_attempts': 3
    },
    'notification': {
        'retry_attempts': 3,
        'retry_delay': 5,
        'batch_size': 10
    }
}
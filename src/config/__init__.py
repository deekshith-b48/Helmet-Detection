"""
Configuration module for Helmet Detection System.
Handles all configuration settings and constants.
"""

from .settings import load_config, save_config, update_config
from .constants import *

__all__ = [
    'load_config',
    'save_config',
    'update_config',
    'MODEL_CONFIG',
    'DETECTION_CONFIG',
    'DATABASE_CONFIG',
    'EMAIL_CONFIG',
    'PROCESSING_CONFIG',
    'PATHS',
    'VIOLATION_TYPES'
]

def get_default_config():
    """Get default configuration settings"""
    return {
        'model': MODEL_CONFIG,
        'detection': DETECTION_CONFIG,
        'database': DATABASE_CONFIG,
        'email': EMAIL_CONFIG,
        'processing': PROCESSING_CONFIG,
        'paths': PATHS
    }

def validate_config(config):
    """Validate configuration settings"""
    required_keys = [
        'model',
        'detection',
        'database',
        'email',
        'processing',
        'paths'
    ]
    
    # Check for required keys
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
            
    # Validate paths
    for path_key, path_value in config['paths'].items():
        if not isinstance(path_value, (str, Path)):
            raise ValueError(f"Invalid path value for {path_key}")
            
    return True
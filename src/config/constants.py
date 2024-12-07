"""
System-wide constants for Helmet Detection System.
"""

from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / 'models'
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# Path configurations
PATHS = {
    'BASE_DIR': BASE_DIR,
    'MODELS_DIR': MODELS_DIR,
    'DATA_DIR': DATA_DIR,
    'LOGS_DIR': LOGS_DIR,
    'VIOLATIONS_DIR': DATA_DIR / 'violations',
    'DATABASE_PATH': DATA_DIR / 'traffic.db',
    'CONFIG_PATH': BASE_DIR / 'config.yaml'
}

# Model configuration
MODEL_CONFIG = {
    'MODEL_PATH': MODELS_DIR / 'frozen_inference_graph.pb',
    'LABEL_MAP_PATH': MODELS_DIR / 'labelmap.pbtxt',
    'INPUT_SIZE': (416, 416),
    'CHANNELS': 3,
    'BATCH_SIZE': 1
}

# Detection configuration
DETECTION_CONFIG = {
    'MIN_CONFIDENCE': 0.5,
    'NMS_THRESHOLD': 0.4,
    'MAX_DETECTIONS': 100,
    'CLASSES': {
        1: 'helmet',
        2: 'no_helmet',
        3: 'motorcycle',
        4: 'license_plate'
    }
}

# Database configuration
DATABASE_CONFIG = {
    'DB_PATH': PATHS['DATABASE_PATH'],
    'POOL_SIZE': 5,
    'TIMEOUT': 30,
    'ENABLE_FOREIGN_KEYS': True
}

# Email configuration
EMAIL_CONFIG = {
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
    'SENDER_EMAIL': os.getenv('SENDER_EMAIL', ''),
    'SENDER_PASSWORD': os.getenv('SENDER_PASSWORD', ''),
    'USE_TLS': True,
    'RETRY_COUNT': 3,
    'RETRY_DELAY': 5
}

# Processing configuration
PROCESSING_CONFIG = {
    'FRAME_SKIP': 2,
    'BUFFER_SIZE': 10,
    'ENABLE_DENOISING': True,
    'ENABLE_ENHANCEMENT': True,
    'NORMALIZE': True,
    'SWAP_RGB': True
}

# Violation types and fines
VIOLATION_TYPES = {
    'NO_HELMET': {
        'code': 'VIO001',
        'description': 'Riding without helmet',
        'fine_amount': 100.00,
        'severity': 'high'
    },
    'TRIPLE_RIDING': {
        'code': 'VIO002',
        'description': 'Triple riding on motorcycle',
        'fine_amount': 150.00,
        'severity': 'medium'
    },
    'NO_LICENSE_PLATE': {
        'code': 'VIO003',
        'description': 'Missing or unreadable license plate',
        'fine_amount': 200.00,
        'severity': 'high'
    }
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'app.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
"""
Core module for Helmet Detection System.
Contains the main processing and detection components.
"""

from .model import YOLOModel, DetectionModel
from .detector import ViolationDetector, LicensePlateDetector
from .processor import ImageProcessor, VideoProcessor, FrameProcessor

__version__ = '1.0.0'

__all__ = [
    'YOLOModel',
    'DetectionModel',
    'ViolationDetector',
    'LicensePlateDetector',
    'ImageProcessor',
    'VideoProcessor',
    'FrameProcessor'
]

# Default configuration for core components
DEFAULT_CONFIG = {
    'IMAGE_SIZE': (416, 416),
    'BATCH_SIZE': 1,
    'CONFIDENCE_THRESHOLD': 0.5,
    'NMS_THRESHOLD': 0.4,
    'MAX_DETECTION_INSTANCES': 100
}

def get_version():
    """Return the current version of the core module"""
    return __version__

def get_default_config():
    """Return default configuration for core components"""
    return DEFAULT_CONFIG.copy()
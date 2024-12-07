import cv2
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from core.detector import ViolationDetector, LicensePlateDetector
from utils.database import DatabaseManager
from utils.notifier import EmailNotifier
from config.settings import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HelmetDetectionSystem:
    """Main application class for helmet detection system"""
    
    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.setup_components()
        
        # Create required directories
        self.setup_directories()
        
    def setup_components(self):
        """Initialize system components"""
        try:
            self.violation_detector = ViolationDetector(self.config)
            self.plate_detector = LicensePlateDetector(self.config)
            self.db_manager = DatabaseManager(self.config)
            self.email_notifier = EmailNotifier(self.config)
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
            
    def setup_directories(self):
        """Create necessary directories"""
        dirs = ['violations', 'logs', 'data']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)
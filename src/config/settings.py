"""
Settings management for Helmet Detection System.
Handles loading, saving, and updating configuration settings.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional, Union
from .constants import PATHS, MODEL_CONFIG, DETECTION_CONFIG, DATABASE_CONFIG, EMAIL_CONFIG

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Manages configuration settings for the system"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else PATHS['CONFIG_PATH']
        self.config = {}
        self.load_config()

    def load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.config = self._get_default_config()
                self.save_config()
                logger.info("Default configuration created")
                
            return self.config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def update_config(self, updates: Dict):
        """Update configuration with new values"""
        try:
            # Deep update of configuration
            self._deep_update(self.config, updates)
            self.save_config()
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise

    def _deep_update(self, d: Dict, u: Dict):
        """Recursively update dictionary"""
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def _get_default_config(self) -> Dict:
        """Get default configuration settings"""
        return {
            'model': MODEL_CONFIG,
            'detection': DETECTION_CONFIG,
            'database': DATABASE_CONFIG,
            'email': EMAIL_CONFIG
        }

    def validate_config(self) -> bool:
        """Validate current configuration"""
        try:
            required_sections = ['model', 'detection', 'database', 'email']
            
            # Check required sections
            for section in required_sections:
                if section not in self.config:
                    raise ValueError(f"Missing required section: {section}")
                    
            # Validate model configuration
            model_config = self.config['model']
            if not Path(model_config['MODEL_PATH']).exists():
                raise ValueError(f"Model file not found: {model_config['MODEL_PATH']}")
                
            # Validate database configuration
            db_config = self.config['database']
            db_path = Path(db_config['DB_PATH'])
            if not db_path.parent.exists():
                db_path.parent.mkdir(parents=True)
                
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def get_section(self, section: str) -> Dict:
        """Get specific configuration section"""
        if section not in self.config:
            raise KeyError(f"Configuration section not found: {section}")
        return self.config[section]

# Global configuration manager instance
config_manager = ConfigurationManager()

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict:
    """Load configuration settings"""
    if config_path:
        global config_manager
        config_manager = ConfigurationManager(config_path)
    return config_manager.config

def save_config():
    """Save current configuration"""
    config_manager.save_config()

def update_config(updates: Dict):
    """Update configuration with new values"""
    config_manager.update_config(updates)

def get_config_section(section: str) -> Dict:
    """Get specific configuration section"""
    return config_manager.get_section(section)
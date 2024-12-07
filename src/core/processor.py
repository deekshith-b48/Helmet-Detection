import cv2
import numpy as np
from typing import Tuple, List, Dict, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """Abstract base class for all processors"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.target_size = config.get('IMAGE_SIZE', (416, 416))
        self.normalize = config.get('NORMALIZE', True)
        self.swap_rgb = config.get('SWAP_RGB', True)

    @abstractmethod
    def process(self, input_data: np.ndarray) -> np.ndarray:
        """Process input data"""
        pass

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Common preprocessing steps"""
        try:
            # Resize image
            processed = cv2.resize(image, self.target_size)
            
            # Normalize if required
            if self.normalize:
                processed = processed.astype(np.float32) / 255.0
                
            # Swap RGB if required
            if self.swap_rgb:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
                
            return processed
        except Exception as e:
            logger.error(f"Error in preprocessing: {e}")
            raise

class ImageProcessor(BaseProcessor):
    """Processor for single images"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.augmentation = config.get('AUGMENTATION', False)

    def process(self, image: np.ndarray) -> np.ndarray:
        """Process a single image"""
        try:
            # Basic preprocessing
            processed = self.preprocess(image)
            
            # Apply augmentation if enabled
            if self.augmentation:
                processed = self.apply_augmentation(processed)
                
            return processed
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise

    def apply_augmentation(self, image: np.ndarray) -> np.ndarray:
        """Apply augmentation techniques"""
        try:
            # Random brightness adjustment
            if np.random.rand() > 0.5:
                delta = 30
                image = image + np.random.uniform(-delta, delta)
                image = np.clip(image, 0, 255)
                
            # Random contrast adjustment
            if np.random.rand() > 0.5:
                factor = np.random.uniform(0.5, 1.5)
                image = image * factor
                image = np.clip(image, 0, 255)
                
            return image
        except Exception as e:
            logger.error(f"Error in augmentation: {e}")
            raise

class VideoProcessor(BaseProcessor):
    """Processor for video streams"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.frame_skip = config.get('FRAME_SKIP', 0)
        self.buffer_size = config.get('BUFFER_SIZE', 10)
        self.frame_buffer = []
        self.frame_count = 0

    def process(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process a video frame"""
        try:
            # Frame skipping
            self.frame_count += 1
            if self.frame_skip and self.frame_count % (self.frame_skip + 1) != 0:
                return None
                
            # Basic preprocessing
            processed = self.preprocess(frame)
            
            # Buffer management
            self.update_buffer(processed)
            
            return processed
        except Exception as e:
            logger.error(f"Error processing video frame: {e}")
            raise

    def update_buffer(self, frame: np.ndarray):
        """Update frame buffer"""
        self.frame_buffer.append(frame)
        if len(self.frame_buffer) > self.buffer_size:
            self.frame_buffer.pop(0)

    def get_buffer_average(self) -> np.ndarray:
        """Calculate average frame from buffer"""
        if not self.frame_buffer:
            return None
        return np.mean(self.frame_buffer, axis=0).astype(np.uint8)

class FrameProcessor:
    """High-level processor combining multiple processing steps"""
    
    def __init__(self, config: Dict):
        self.image_processor = ImageProcessor(config)
        self.video_processor = VideoProcessor(config)
        self.processing_pipeline = self.setup_pipeline(config)

    def setup_pipeline(self, config: Dict) -> List:
        """Setup processing pipeline based on configuration"""
        pipeline = []
        
        # Add processing steps based on config
        if config.get('ENABLE_DENOISING', True):
            pipeline.append(self.denoise_frame)
        if config.get('ENABLE_ENHANCEMENT', True):
            pipeline.append(self.enhance_frame)
        
        return pipeline

    def process_frame(self, frame: np.ndarray, is_video: bool = True) -> np.ndarray:
        """Process a frame through the complete pipeline"""
        try:
            # Choose appropriate processor
            processor = self.video_processor if is_video else self.image_processor
            
            # Initial processing
            processed = processor.process(frame)
            if processed is None:
                return None
                
            # Apply pipeline steps
            for step in self.processing_pipeline:
                processed = step(processed)
                
            return processed
        except Exception as e:
            logger.error(f"Error in frame processing pipeline: {e}")
            raise

    @staticmethod
    def denoise_frame(frame: np.ndarray) -> np.ndarray:
        """Apply denoising to frame"""
        return cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)

    @staticmethod
    def enhance_frame(frame: np.ndarray) -> np.ndarray:
        """Enhance frame quality"""
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        
        # Merge channels
        enhanced_lab = cv2.merge((cl,a,b))
        
        # Convert back to BGR
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced_bgr
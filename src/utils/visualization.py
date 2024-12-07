"""
Visualization utilities for Helmet Detection System.
Handles drawing boxes, labels, and information on frames.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Union
import logging

logger = logging.getLogger(__name__)

class Visualizer:
    def __init__(self, config: Dict):
        """Initialize visualizer with configuration"""
        self.config = config
        self.colors = config['colors']
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = config['font_scale']
        self.thickness = config['thickness']
        
    def draw_detection(self, 
                      frame: np.ndarray,
                      detection: Dict,
                      label: str = None,
                      color: Tuple[int, int, int] = None) -> np.ndarray:
        """Draw a single detection on frame"""
        try:
            # Get coordinates
            x1, y1, x2, y2 = self._get_coordinates(detection['bbox'], frame.shape)
            
            # Draw box
            color = color or self.colors['red']
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, self.thickness)
            
            # Draw label if provided
            if label:
                self._draw_label(frame, label, (x1, y1), color)
                
            return frame
        except Exception as e:
            logger.error(f"Error drawing detection: {e}")
            return frame
            
    def draw_violations(self, 
                       frame: np.ndarray,
                       violations: List[Dict]) -> np.ndarray:
        """Draw all violations on frame"""
        try:
            for violation in violations:
                # Draw violation box
                frame = self.draw_detection(
                    frame,
                    violation,
                    f"{violation['type']}: {violation['confidence']:.2f}",
                    self.colors['red']
                )
                
                # Draw license plate if available
                if 'license_plate' in violation:
                    self._draw_plate_info(frame, violation)
                    
            # Draw summary
            if violations:
                self._draw_summary(frame, violations)
                
            return frame
        except Exception as e:
            logger.error(f"Error drawing violations: {e}")
            return frame
            
    def _draw_label(self,
                    frame: np.ndarray,
                    text: str,
                    position: Tuple[int, int],
                    color: Tuple[int, int, int]):
        """Draw text label on frame"""
        try:
            # Get text size
            text_size = cv2.getTextSize(
                text, 
                self.font,
                self.font_scale,
                self.thickness
            )[0]
            
            # Draw background rectangle
            cv2.rectangle(
                frame,
                position,
                (position[0] + text_size[0], position[1] - text_size[1] - 5),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                frame,
                text,
                (position[0], position[1] - 5),
                self.font,
                self.font_scale,
                (255, 255, 255),
                self.thickness
            )
        except Exception as e:
            logger.error(f"Error drawing label: {e}")
            
    def _draw_plate_info(self,
                        frame: np.ndarray,
                        violation: Dict):
        """Draw license plate information"""
        try:
            if 'plate_bbox' in violation:
                # Draw plate box
                plate_bbox = violation['plate_bbox']
                x1, y1, x2, y2 = self._get_coordinates(plate_bbox, frame.shape)
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    self.colors['blue'],
                    self.thickness
                )
                
                # Draw plate number
                plate_text = f"Plate: {violation['license_plate']}"
                self._draw_label(
                    frame,
                    plate_text,
                    (x1, y1 - 25),
                    self.colors['blue']
                )
        except Exception as e:
            logger.error(f"Error drawing plate info: {e}")
            
    def _draw_summary(self,
                     frame: np.ndarray,
                     violations: List[Dict]):
        """Draw violation summary"""
        try:
            # Prepare summary text
            summary = f"Violations: {len(violations)}"
            
            # Draw at top-left corner
            cv2.putText(
                frame,
                summary,
                (10, 30),
                self.font,
                1,
                self.colors['red'],
                2
            )
        except Exception as e:
            logger.error(f"Error drawing summary: {e}")
            
    @staticmethod
    def _get_coordinates(bbox: Union[List, Tuple],
                        frame_shape: Tuple[int, ...]) -> Tuple[int, int, int, int]:
        """Convert bbox to absolute coordinates"""
        height, width = frame_shape[:2]
        
        if len(bbox) == 4:
            if max(bbox) <= 1.0:  # Normalized coordinates
                x1 = int(bbox[0] * width)
                y1 = int(bbox[1] * height)
                x2 = int(bbox[2] * width)
                y2 = int(bbox[3] * height)
            else:  # Absolute coordinates
                x1, y1, x2, y2 = map(int, bbox)
        else:
            raise ValueError("Invalid bbox format")
            
        return x1, y1, x2, y2
        
    def add_timestamp(self,
                     frame: np.ndarray,
                     timestamp: str) -> np.ndarray:
        """Add timestamp to frame"""
        try:
            cv2.putText(
                frame,
                timestamp,
                (10, frame.shape[0] - 10),
                self.font,
                0.5,
                (255, 255, 255),
                1
            )
            return frame
        except Exception as e:
            logger.error(f"Error adding timestamp: {e}")
            return frame
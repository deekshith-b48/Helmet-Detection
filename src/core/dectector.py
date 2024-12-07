import cv2
import numpy as np
from typing import List, Dict, Tuple
from .model import DetectionModel
from ..utils.visualization import Visualizer

class ViolationDetector:
    """Main detector class for helmet violations"""
    
    def __init__(self, config: Dict):
        self.model = DetectionModel(config)
        self.visualizer = Visualizer()
        self.min_confidence = config['MIN_CONFIDENCE']
        self.violation_rules = config['VIOLATION_RULES']
        
    def process_frame(self, frame: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """Process a frame and detect violations"""
        # Get detections
        detections, processed_frame = self.model.process_frame(frame)
        
        # Check for violations
        violations = self._check_violations(detections)
        
        # Draw detections and violations
        if violations:
            processed_frame = self.visualizer.draw_violations(
                processed_frame,
                violations
            )
            
        return violations, processed_frame
        
    def _check_violations(self, detections: List[Dict]) -> List[Dict]:
        """Check for helmet violations"""
        violations = []
        riders = []
        helmets = []
        
        # Separate detections by class
        for detection in detections:
            if detection['confidence'] < self.min_confidence:
                continue
                
            if detection['class_name'] == 'rider':
                riders.append(detection)
            elif detection['class_name'] == 'helmet':
                helmets.append(detection)
                
        # Check for violations based on rules
        if len(riders) > len(helmets):
            for rider in riders:
                # Check if rider has a nearby helmet
                if not self._has_nearby_helmet(rider, helmets):
                    violations.append({
                        'type': 'no_helmet',
                        'confidence': rider['confidence'],
                        'bbox': rider['bbox'],
                        'rider_detection': rider
                    })
                    
        return violations
        
    def _has_nearby_helmet(self, rider: Dict, helmets: List[Dict]) -> bool:
        """Check if a rider has a nearby helmet"""
        rider_center = self._get_bbox_center(rider['bbox'])
        
        for helmet in helmets:
            helmet_center = self._get_bbox_center(helmet['bbox'])
            distance = np.linalg.norm(
                np.array(rider_center) - np.array(helmet_center)
            )
            
            if distance < self.violation_rules['MAX_HELMET_DISTANCE']:
                return True
                
        return False
        
    @staticmethod
    def _get_bbox_center(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Get center point of bounding box"""
        x, y, w, h = bbox
        return (x + w//2, y + h//2)

class LicensePlateDetector:
    """License plate detection and OCR"""
    
    def __init__(self, config: Dict):
        self.ocr_config = config['OCR_CONFIG']
        self.min_plate_area = config['MIN_PLATE_AREA']
        self.plate_aspect_ratio = config['PLATE_ASPECT_RATIO']
        
    def detect_plate(self, frame: np.ndarray) -> Tuple[str, Tuple[int, int, int, int]]:
        """Detect and read license plate"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply filters
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.threshold(
            blur, 0, 255, 
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]
        
        # Find contours
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Check each contour for license plate
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_plate_area:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                
                if abs(aspect_ratio - self.plate_aspect_ratio) < 0.5:
                    # Extract plate region
                    plate_region = thresh[y:y+h, x:x+w]
                    
                    # Perform OCR
                    try:
                        plate_text = self._perform_ocr(plate_region)
                        if self._validate_plate(plate_text):
                            return plate_text, (x, y, w, h)
                    except Exception as e:
                        print(f"OCR Error: {e}")
                        continue
                        
        return None, None
        
    def _perform_ocr(self, image: np.ndarray) -> str:
        """Perform OCR on plate image"""
        # Implementation depends on OCR library (e.g., Tesseract)
        # Return cleaned and formatted plate text
        pass
        
    def _validate_plate(self, plate_text: str) -> bool:
        """Validate license plate format"""
        # Implement validation logic based on plate format rules
        pass
import pytest
import cv2
import numpy as np
from pathlib import Path
from src.core.detector import ViolationDetector
from src.utils.visualization import Visualizer

@pytest.fixture
def detector():
    config = {
        'MODEL_PATH': 'models/weights/frozen_inference_graph.pb',
        'LABEL_MAP_PATH': 'models/yolo/data/helmet.names',
        'MIN_CONFIDENCE': 0.5
    }
    return ViolationDetector(config)

@pytest.fixture
def test_image():
    img_path = Path('tests/data/test_image.jpg')
    return cv2.imread(str(img_path))

class TestViolationDetector:
    def test_initialization(self, detector):
        assert detector.model is not None
        assert detector.min_confidence == 0.5

    def test_preprocess_image(self, detector, test_image):
        processed = detector.preprocess_image(test_image)
        assert isinstance(processed, np.ndarray)
        assert processed.shape[-1] == 3  # RGB channels

    def test_detect_objects(self, detector, test_image):
        detections = detector.detect_objects(test_image)
        assert isinstance(detections, list)
        
        if len(detections) > 0:
            detection = detections[0]
            assert 'bbox' in detection
            assert 'confidence' in detection
            assert 'class_id' in detection

    def test_check_helmet_violation(self, detector, test_image):
        # Detect objects
        detections = detector.detect_objects(test_image)
        
        # Check for violations
        violations = detector.check_violations(detections)
        assert isinstance(violations, list)
        
        if len(violations) > 0:
            violation = violations[0]
            assert 'type' in violation
            assert 'confidence' in violation
            assert violation['type'] in ['no_helmet', 'triple_riding']

    @pytest.mark.parametrize("confidence_threshold", [0.3, 0.5, 0.7])
    def test_different_confidence_thresholds(self, detector, test_image, confidence_threshold):
        detector.min_confidence = confidence_threshold
        detections = detector.detect_objects(test_image)
        
        # Verify all detections meet the threshold
        for detection in detections:
            assert detection['confidence'] >= confidence_threshold

    def test_multiple_violations(self, detector):
        # Load test image with multiple violations
        img_path = Path('tests/data/multiple_violations.jpg')
        image = cv2.imread(str(img_path))
        
        detections = detector.detect_objects(image)
        violations = detector.check_violations(detections)
        
        # Verify multiple violations are detected
        assert len(violations) > 1
        
        # Verify violation types
        violation_types = [v['type'] for v in violations]
        assert 'no_helmet' in violation_types

    def test_no_violations(self, detector):
        # Load compliant image (with helmet)
        img_path = Path('tests/data/compliant_rider.jpg')
        image = cv2.imread(str(img_path))
        
        detections = detector.detect_objects(image)
        violations = detector.check_violations(detections)
        
        # Verify no violations are detected
        assert len(violations) == 0

    def test_visualization(self, detector, test_image):
        # Get detections and violations
        detections = detector.detect_objects(test_image)
        violations = detector.check_violations(detections)
        
        # Create visualizer
        visualizer = Visualizer()
        
        # Draw detections
        annotated_image = visualizer.draw_detections(
            test_image.copy(), 
            detections,
            violations
        )
        
        # Verify image was modified
        assert not np.array_equal(test_image, annotated_image)
        
    @pytest.mark.skip(reason="GPU required")
    def test_gpu_detection(self, detector, test_image):
        # Test GPU acceleration if available
        import tensorflow as tf
        if tf.test.is_built_with_cuda():
            detections = detector.detect_objects(test_image)
            assert len(detections) > 0
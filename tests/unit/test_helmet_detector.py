import unittest
from unittest.mock import patch, MagicMock
import yaml
import os
import torch
import numpy as np
from src.core.helmet_detector import YOLOHelmetDetector

# Helper to create a dummy config file for tests
def create_dummy_config_file(config_path, model_config_data):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump({'model': model_config_data}, f)

# Helper to create a dummy empty model file
def create_dummy_model_file(model_path):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'w') as f:
        f.write("dummy model content") # Content doesn't matter for mocked YOLO

class TestYOLOHelmetDetector(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_temp_config_models"
        os.makedirs(self.test_dir, exist_ok=True)

        self.dummy_config_path = os.path.join(self.test_dir, "dummy_config.yaml")
        self.dummy_model_path = os.path.join(self.test_dir, "dummy_model.pt")

        # Default config for most tests
        self.default_model_config = {
            'name': 'yolov8n_test.pt',
            'path': self.dummy_model_path,
            'confidence_threshold': 0.25,
            'iou_threshold': 0.45,
            'classes': {'person': 0, 'helmet': 1}
        }
        create_dummy_config_file(self.dummy_config_path, self.default_model_config)
        create_dummy_model_file(self.dummy_model_path)

    def tearDown(self):
        # Clean up dummy files and directory
        if os.path.exists(self.dummy_config_path):
            os.remove(self.dummy_config_path)
        if os.path.exists(self.dummy_model_path):
            os.remove(self.dummy_model_path)
        if os.path.exists(self.test_dir):
            # Check if directory is empty before removing, or use shutil.rmtree
            if not os.listdir(self.test_dir): # Only remove if empty
                 os.rmdir(self.test_dir)
            else: # If other files were created, more robust cleanup might be needed
                 import shutil
                 shutil.rmtree(self.test_dir, ignore_errors=True)


    @patch('src.core.helmet_detector.YOLO') # Mock the YOLO class from ultralytics
    def test_initialization_loads_config_and_model(self, MockYOLO):
        mock_yolo_instance = MockYOLO.return_value
        mock_yolo_instance.names = {0: 'person', 1: 'helmet'} # Simulate model's class names

        detector = YOLOHelmetDetector(config_path=self.dummy_config_path)

        MockYOLO.assert_called_once_with(self.dummy_model_path) # Check YOLO was called with model path
        mock_yolo_instance.to.assert_called_once() # Check model was moved to device
        mock_yolo_instance.fuse.assert_called_once() # Check model was fused

        self.assertEqual(detector.confidence_threshold, 0.25)
        self.assertEqual(detector.iou_threshold, 0.45)
        self.assertEqual(detector.active_classes, {'person': 0, 'helmet': 1})
        self.assertEqual(detector.class_id_to_name, {0: 'person', 1: 'helmet'})

    @patch('src.core.helmet_detector.YOLO')
    def test_initialization_fallback_to_model_name_if_path_not_exist(self, MockYOLO):
        mock_yolo_instance = MockYOLO.return_value
        mock_yolo_instance.names = {0: 'person', 1: 'bicycle'} # COCO names for yolov8n.pt

        # Create config that points to a non-existent model path, but has a valid model_name
        config_data = self.default_model_config.copy()
        non_existent_model_path = os.path.join(self.test_dir,"non_existent.pt")
        config_data['path'] = non_existent_model_path
        config_data['name'] = 'yolov8n.pt' # This should be used as fallback
        create_dummy_config_file(self.dummy_config_path, config_data)

        detector = YOLOHelmetDetector(config_path=self.dummy_config_path)

        MockYOLO.assert_called_once_with('yolov8n.pt') # YOLO should be called with model_name
        self.assertEqual(detector.model_name, 'yolov8n.pt')

    @patch('src.core.helmet_detector.YOLO')
    def test_detect_method_processes_predictions(self, MockYOLO):
        mock_yolo_instance = MockYOLO.return_value
        # Simulate the structure of ultralytics YOLO prediction results
        # Each result object has a 'boxes' attribute
        mock_result = MagicMock()
        # Each box object has xyxy, conf, cls attributes, all as tensors
        mock_box1 = MagicMock()
        mock_box1.xyxy = torch.tensor([[10, 20, 30, 40]])
        mock_box1.conf = torch.tensor([0.9])
        mock_box1.cls = torch.tensor([0]) # Class ID 0 (person)

        mock_box2 = MagicMock()
        mock_box2.xyxy = torch.tensor([[50, 60, 70, 80]])
        mock_box2.conf = torch.tensor([0.8])
        mock_box2.cls = torch.tensor([1]) # Class ID 1 (helmet)

        mock_result.boxes = [mock_box1, mock_box2]
        mock_yolo_instance.predict.return_value = [mock_result] # predict returns a list of results

        # Setup detector with known class mapping
        detector = YOLOHelmetDetector(config_path=self.dummy_config_path)
        # Ensure class_id_to_name is set as expected by the setUp's default config
        self.assertEqual(detector.class_id_to_name, {0: 'person', 1: 'helmet'})

        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8) # Frame content doesn't matter due to mocking
        detections = detector.detect(dummy_frame)

        mock_yolo_instance.predict.assert_called_once_with(
            source=dummy_frame,
            conf=detector.confidence_threshold,
            iou=detector.iou_threshold,
            verbose=False
        )

        self.assertEqual(len(detections), 2)
        self.assertEqual(detections[0]['box'], [10, 20, 30, 40])
        self.assertEqual(detections[0]['confidence'], 0.9)
        self.assertEqual(detections[0]['class_id'], 0)
        self.assertEqual(detections[0]['class_name'], 'person') # From class_id_to_name mapping

        self.assertEqual(detections[1]['box'], [50, 60, 70, 80])
        self.assertEqual(detections[1]['confidence'], 0.8)
        self.assertEqual(detections[1]['class_id'], 1)
        self.assertEqual(detections[1]['class_name'], 'helmet')

    @patch('src.core.helmet_detector.YOLO')
    def test_detect_method_handles_no_detections(self, MockYOLO):
        mock_yolo_instance = MockYOLO.return_value
        mock_result = MagicMock()
        mock_result.boxes = None # No boxes detected
        mock_yolo_instance.predict.return_value = [mock_result]

        detector = YOLOHelmetDetector(config_path=self.dummy_config_path)
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detections = detector.detect(dummy_frame)

        self.assertEqual(len(detections), 0)

    @patch('src.core.helmet_detector.YOLO')
    def test_initialization_with_missing_classes_in_config_uses_model_names(self, MockYOLO):
        mock_yolo_instance = MockYOLO.return_value
        # Simulate a model that has its own class names
        mock_yolo_instance.names = {0: 'car', 1: 'truck', 7: 'person_model_defined'} # Example model names

        config_data_no_classes = {
            'name': 'yolov8_custom_test.pt',
            'path': self.dummy_model_path, # Must exist
            'confidence_threshold': 0.3,
            'iou_threshold': 0.5,
            # 'classes' key is deliberately missing here
        }
        create_dummy_config_file(self.dummy_config_path, config_data_no_classes)
        create_dummy_model_file(self.dummy_model_path) # Ensure model file exists

        detector = YOLOHelmetDetector(config_path=self.dummy_config_path)

        MockYOLO.assert_called_once_with(self.dummy_model_path)
        # Check that active_classes and class_id_to_name were populated from model.names
        self.assertEqual(detector.active_classes, {0: 'car', 1: 'truck', 7: 'person_model_defined'})
        self.assertEqual(detector.class_id_to_name, {'car':0, 'truck':1, 'person_model_defined':7}) # This should be id:name
        self.assertEqual(detector.class_id_to_name, {v: k for k,v in mock_yolo_instance.names.items()})


if __name__ == '__main__':
    unittest.main()
```

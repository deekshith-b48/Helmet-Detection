import unittest
import yaml
import os
from src.core.violation_detector import ViolationDetector

# Helper to create a dummy config file for tests
def create_dummy_vd_config_file(config_path, model_config_data):
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    # ViolationDetector expects the full config structure, so nest model_config_data under 'model'
    full_config = {'model': model_config_data}
    with open(config_path, 'w') as f:
        yaml.dump(full_config, f)

class TestViolationDetector(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_temp_vd_configs"
        os.makedirs(self.test_dir, exist_ok=True)
        self.dummy_config_path = os.path.join(self.test_dir, "dummy_vd_config.yaml")

    def tearDown(self):
        if os.path.exists(self.dummy_config_path):
            os.remove(self.dummy_config_path)
        if os.path.exists(self.test_dir):
            if not os.listdir(self.test_dir):
                 os.rmdir(self.test_dir)
            else:
                 import shutil
                 shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        model_config_data = {
            'active_class_set_type': 'coco',
            'classes': {'person': 0},
            'violation_relevant_classes': {'person': 'person'}
        }
        create_dummy_vd_config_file(self.dummy_config_path, model_config_data)

        detector = ViolationDetector(config_path=self.dummy_config_path)
        self.assertEqual(detector.active_class_set_type, 'coco')
        self.assertEqual(detector.configured_classes, {'person': 0})
        self.assertEqual(detector.violation_relevant_config, {'person': 'person'})

    def test_detect_violations_coco_person_sighting(self):
        model_config_data = {
            'active_class_set_type': 'coco',
            'classes': {'person': 0, 'car': 2},
            'violation_relevant_classes': {'person': 'person'} # Only 'person' is relevant
        }
        create_dummy_vd_config_file(self.dummy_config_path, model_config_data)
        detector = ViolationDetector(config_path=self.dummy_config_path)

        detections = [
            {'box': [10,10,20,20], 'confidence': 0.9, 'class_id': 0, 'class_name': 'person'},
            {'box': [30,30,40,40], 'confidence': 0.8, 'class_id': 2, 'class_name': 'car'}, # Not relevant
            {'box': [50,50,60,60], 'confidence': 0.95, 'class_id': 0, 'class_name': 'person'}
        ]
        violations = detector.detect_violations(detections)

        self.assertEqual(len(violations), 2)
        for viol in violations:
            self.assertEqual(viol['class_name'], 'person')
            self.assertEqual(viol['violation_type'], 'person_sighting')

    def test_detect_violations_custom_helmet_model_no_helmet(self):
        model_config_data = {
            'active_class_set_type': 'custom_helmet',
            'classes': {'helmet': 0, 'no_helmet': 1, 'head': 2},
            'violation_relevant_classes': {'no_helmet': 'no_helmet', 'head': 'head_sighting'}
        }
        create_dummy_vd_config_file(self.dummy_config_path, model_config_data)
        detector = ViolationDetector(config_path=self.dummy_config_path)

        detections = [
            {'box': [10,10,20,20], 'confidence': 0.9, 'class_id': 1, 'class_name': 'no_helmet'},
            {'box': [30,30,40,40], 'confidence': 0.8, 'class_id': 0, 'class_name': 'helmet'}, # Not a violation class
            {'box': [50,50,60,60], 'confidence': 0.95, 'class_id': 2, 'class_name': 'head'}
        ]
        violations = detector.detect_violations(detections)

        self.assertEqual(len(violations), 2)
        # Check first violation (no_helmet)
        self.assertEqual(violations[0]['class_name'], 'no_helmet')
        self.assertEqual(violations[0]['violation_type'], 'helmet_violation')
        # Check second violation (head)
        self.assertEqual(violations[1]['class_name'], 'head')
        # The current logic in ViolationDetector sets violation_type to 'helmet_violation'
        # if active_class_set_type is 'custom_helmet' and class_name is in violation_relevant_config.
        # This might need refinement if 'head' should have a different violation_type string.
        # For now, testing current behavior:
        self.assertEqual(violations[1]['violation_type'], 'helmet_violation')


    def test_detect_violations_custom_helmet_model_only_helmet(self):
        model_config_data = {
            'active_class_set_type': 'custom_helmet',
            'classes': {'helmet': 0, 'no_helmet': 1},
            'violation_relevant_classes': {'no_helmet': 'no_helmet'}
        }
        create_dummy_vd_config_file(self.dummy_config_path, model_config_data)
        detector = ViolationDetector(config_path=self.dummy_config_path)

        detections = [
            {'box': [30,30,40,40], 'confidence': 0.8, 'class_id': 0, 'class_name': 'helmet'}
        ]
        violations = detector.detect_violations(detections)
        self.assertEqual(len(violations), 0) # No 'no_helmet' detections

    def test_detect_violations_no_relevant_classes_detected(self):
        model_config_data = {
            'active_class_set_type': 'coco',
            'classes': {'person': 0, 'car': 2},
            'violation_relevant_classes': {'person': 'person'}
        }
        create_dummy_vd_config_file(self.dummy_config_path, model_config_data)
        detector = ViolationDetector(config_path=self.dummy_config_path)

        detections = [
            {'box': [30,30,40,40], 'confidence': 0.8, 'class_id': 2, 'class_name': 'car'}
        ]
        violations = detector.detect_violations(detections)
        self.assertEqual(len(violations), 0)

    def test_detect_violations_empty_detections_list(self):
        model_config_data = {
            'active_class_set_type': 'coco',
            'classes': {'person': 0},
            'violation_relevant_classes': {'person': 'person'}
        }
        create_dummy_vd_config_file(self.dummy_config_path, model_config_data)
        detector = ViolationDetector(config_path=self.dummy_config_path)

        violations = detector.detect_violations([])
        self.assertEqual(len(violations), 0)

if __name__ == '__main__':
    unittest.main()
```

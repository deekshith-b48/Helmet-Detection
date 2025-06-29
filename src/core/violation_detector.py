import yaml

class ViolationDetector:
    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.model_config = self.config.get('model', {})
        self.active_class_set_type = self.model_config.get('active_class_set_type', 'coco')

        # Get the mapping of human-readable class names to their IDs (e.g., {'person': 0, 'helmet': 1})
        self.configured_classes = self.model_config.get('classes', {})

        # Get the list/dict of class names that are relevant for causing a violation
        # e.g. for COCO: {'person': 'person_sighting'}
        # e.g. for Custom: {'no_helmet': 'helmet_violation', 'head_without_helmet': 'helmet_violation'}
        self.violation_relevant_config = self.model_config.get('violation_relevant_classes', {})

        print(f"ViolationDetector initialized. Active class set type: '{self.active_class_set_type}'")
        print(f"Relevant classes for violation: {self.violation_relevant_config}")

    def detect_violations(self, detections):
        """
        Identifies violations based on the detections from YOLOHelmetDetector.

        Args:
            detections (list): A list of detection dictionaries from YOLOHelmetDetector.
                               Each dict: {'box': [x1,y1,x2,y2], 'confidence': conf, 'class_id': id, 'class_name': name}

        Returns:
            list: A list of violation dictionaries. Each dict contains the original
                  detection info plus a 'violation_type' key.
                  e.g., {'box': [...], ..., 'class_name': 'person', 'violation_type': 'person_sighting'}
                  e.g., {'box': [...], ..., 'class_name': 'no_helmet', 'violation_type': 'helmet_violation'}
        """
        violations = []

        for det in detections:
            class_name = det['class_name'] # Human-readable class name from YOLOHelmetDetector

            # Check if this detected class_name is configured as relevant for violations
            if class_name in self.violation_relevant_config:
                violation_type_key = self.violation_relevant_config[class_name] # e.g., "person" or "no_helmet"

                violation_entry = det.copy() # Start with all original detection info

                if self.active_class_set_type == 'coco':
                    # For COCO models, a 'person' detection is the primary event of interest.
                    # We don't know helmet status from this model alone.
                    if class_name == 'person': # Or whatever is configured for person in violation_relevant_classes
                         violation_entry['violation_type'] = 'person_sighting' # Generic term
                         violations.append(violation_entry)

                elif self.active_class_set_type == 'custom_helmet':
                    # For custom helmet models, we look for specific classes like 'no_helmet'.
                    # The key from violation_relevant_config (e.g. "no_helmet") directly implies the violation.
                    # We assume violation_relevant_config for custom models lists actual violation classes.
                    # E.g. violation_relevant_classes: {'no_helmet': 'helmet_violation', 'bare_head': 'helmet_violation'}
                    violation_entry['violation_type'] = 'helmet_violation' # Or map via violation_relevant_config if more detail needed
                    violations.append(violation_entry)

                # Potentially add more sophisticated logic here in the future, e.g.,
                # checking for presence/absence of 'helmet' class near a 'person' detection
                # if the model detects both. For now, it's based on direct class match.

        return violations

if __name__ == '__main__':
    # Basic test for ViolationDetector
    # 1. Create a dummy config (or ensure config/config.yaml is set up for testing)
    # 2. Create dummy detections
    # 3. Run detect_violations and print results

    dummy_config_path = "config/config.yaml" # Use the main config

    # --- Test Case 1: COCO model detecting a person ---
    print("\n--- Test Case 1: COCO model ---")
    # Ensure config/config.yaml is set to 'coco' and 'person' is relevant
    # Example relevant section in config.yaml for this test:
    # model:
    #   active_class_set_type: "coco"
    #   classes:
    #     person: 0
    #     bicycle: 1
    #   violation_relevant_classes:
    #     person: "person" # Indicates 'person' detections are what we look for

    try:
        coco_viol_detector = ViolationDetector(config_path=dummy_config_path)

        # Simulate detections from YOLOHelmetDetector using a COCO model
        dummy_coco_detections = [
            {'box': [10, 10, 50, 50], 'confidence': 0.9, 'class_id': 0, 'class_name': 'person'},
            {'box': [60, 60, 100, 100], 'confidence': 0.8, 'class_id': 1, 'class_name': 'bicycle'} # Not relevant
        ]

        coco_violations = coco_viol_detector.detect_violations(dummy_coco_detections)
        print("COCO Detections:", dummy_coco_detections)
        print("COCO Violations:", coco_violations)
        # Expected: [{'box': [10, 10, 50, 50], ..., 'class_name': 'person', 'violation_type': 'person_sighting'}]
        assert len(coco_violations) == 1
        assert coco_violations[0]['violation_type'] == 'person_sighting'
        assert coco_violations[0]['class_name'] == 'person'

    except FileNotFoundError:
        print(f"ERROR: Config file {dummy_config_path} not found. Cannot run COCO test.")
    except Exception as e:
        print(f"Error during COCO test: {e}")


    # --- Test Case 2: Custom helmet model ---
    print("\n--- Test Case 2: Custom Helmet model ---")
    # For this test, you'd manually edit config.yaml to represent a custom model setup:
    # model:
    #   active_class_set_type: "custom_helmet"
    #   classes:
    #     helmet: 0
    #     no_helmet: 1
    #   violation_relevant_classes:
    #     no_helmet: "no_helmet" # 'no_helmet' class directly indicates a violation

    print(f"Note: For Test Case 2 (Custom Helmet), ensure '{dummy_config_path}' is manually updated to:")
    print("""
    model:
      active_class_set_type: "custom_helmet"
      classes:
        helmet: 0
        no_helmet: 1
      violation_relevant_classes:
        no_helmet: "no_helmet"
    """)
    # This part of the test requires manual config change before running, or a separate test config file.
    # For automated testing, one would typically create a temporary config file for each case.

    # Assuming config is manually set for "custom_helmet" for this part of the test:
    try:
        custom_viol_detector = ViolationDetector(config_path=dummy_config_path) # Re-init with (potentially changed) config

        dummy_custom_detections = [
            {'box': [10, 10, 50, 50], 'confidence': 0.9, 'class_id': 1, 'class_name': 'no_helmet'},
            {'box': [70, 70, 120, 120], 'confidence': 0.95, 'class_id': 0, 'class_name': 'helmet'},
            {'box': [150, 150, 200, 200], 'confidence': 0.85, 'class_id': 1, 'class_name': 'no_helmet'}
        ]

        custom_violations = custom_viol_detector.detect_violations(dummy_custom_detections)
        print("Custom Detections:", dummy_custom_detections)
        print("Custom Violations:", custom_violations)
        # Expected: Two violations of type 'helmet_violation' for 'no_helmet' class
        # This assertion will depend on the config being correctly set for custom_helmet type.
        # If config is still coco, this test will likely fail or produce empty results.
        # assert len(custom_violations) == 2
        # assert all(v['violation_type'] == 'helmet_violation' for v in custom_violations)
        # assert custom_violations[0]['class_name'] == 'no_helmet'
        print("To properly test Case 2, manually edit config.yaml then re-run, or use a separate test config.")

    except FileNotFoundError:
        print(f"ERROR: Config file {dummy_config_path} not found. Cannot run Custom Helmet test.")
    except Exception as e:
        print(f"Error during Custom Helmet test: {e}")

import torch
from ultralytics import YOLO
import cv2
import yaml
import os

class YOLOHelmetDetector:
    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.model_name = self.config['model'].get('name', 'yolov8n.pt') # Default to yolov8n if no name
        self.model_path = self.config['model'].get('path', 'models/yolov8n_helmet.pt') # User specified path
        self.confidence_threshold = self.config['model'].get('confidence_threshold', 0.4)
        self.iou_threshold = self.config['model'].get('iou_threshold', 0.5)

        # Determine the model to load
        # If the specified model_path exists, use it.
        # Otherwise, fall back to model_name (which might be a standard ultralytics model like 'yolov8n.pt')
        load_path = self.model_path
        if not os.path.exists(self.model_path):
            print(f"Warning: Model path {self.model_path} not found. Falling back to standard model {self.model_name}.")
            load_path = self.model_name # e.g., "yolov8n.pt" which ultralytics can download

        try:
            self.model = YOLO(load_path) # Loads the model (downloads if it's a standard name like 'yolov8n.pt' and not present)
            print(f"YOLO Helmet Detector initialized with model: {load_path}")
            self.model.fuse() # Fuse layers for faster inference (optional, but good practice)
        except Exception as e:
            print(f"Error loading YOLO model from {load_path}: {e}")
            # Fallback to a default pretrained model if custom path fails and model_name is also custom
            if load_path != 'yolov8n.pt':
                print("Attempting to load default 'yolov8n.pt' as a last resort.")
                try:
                    self.model = YOLO('yolov8n.pt')
                    print(f"Successfully loaded 'yolov8n.pt'.")
                    self.model.fuse()
                except Exception as e_fallback:
                    print(f"Failed to load default 'yolov8n.pt': {e_fallback}")
                    raise RuntimeError(f"Could not load any YOLO model. Last error: {e_fallback}") from e_fallback
            else:
                 raise RuntimeError(f"Could not load YOLO model {load_path}. Error: {e}") from e


        # Ensure model is on the correct device (GPU if available, else CPU)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        print(f"Model loaded on device: {self.device}")

        # Load class mapping from config
        self.active_classes = self.config['model'].get('classes', {})
        if not self.active_classes:
            print("Warning: No 'model.classes' defined in config. Attempting to use model's internal classes.")
            # Fallback to model's own class names if available
            if hasattr(self.model, 'names'):
                self.active_classes = {name: i for i, name in self.model.names.items()}
                print(f"Using model's internal classes: {self.active_classes}")
            else:
                print("Error: Model has no 'names' attribute and no classes defined in config. Detection might be uninterpretable.")
                self.active_classes = {} # Cannot map IDs to names
        else:
            print(f"Using active classes from config: {self.active_classes}")

        # Create a reverse mapping from class ID to class name for convenience
        self.class_id_to_name = {v: k for k, v in self.active_classes.items()}


    def detect(self, frame):
        """
        Performs helmet detection on a single frame.
        Args:
            frame: A NumPy array representing the image/frame.
        Returns:
            A list of detections. Each detection is a dictionary:
            {'box': [x1, y1, x2, y2], 'confidence': conf, 'class_id': cls_id, 'class_name': cls_name}
        """
        detections_list = []

        # Perform inference
        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False # Reduce console output during inference
        )

        # Process results
        if results and results[0].boxes:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                # Get class name from model's class list
                class_name = self.model.names[cls_id] if hasattr(self.model, 'names') and cls_id in self.model.names else f"class_{cls_id}"

                # If specific target classes are defined (e.g. helmet, no_helmet),
                # and the detected class is one of them, add to list.
                # If no specific target classes (e.g. using generic yolov8n),
                # it might detect 'person'. The violation logic will handle this.
                # For now, we return what the model detects based on its training.

                # If self.model_defined_classes is populated, we might only want to return those.
                # However, for a generic model, we might detect 'person' and then a later stage
                # (or a second model) determines if the person has a helmet.
                # For this step, we'll return all detections and let downstream components filter.

                detections_list.append({
                    'box': [x1, y1, x2, y2],
                    'confidence': conf,
                    'class_id': cls_id,
                    'class_name': class_name
                })

        return detections_list

if __name__ == '__main__':
    # This is for basic testing of the YOLOHelmetDetector
    # Ensure you have 'config/config.yaml' and an image for testing.

    # Create a dummy config for testing if not present
    if not os.path.exists("config/config.yaml"):
        print("Creating dummy config/config.yaml for testing YOLOHelmetDetector.")
        os.makedirs("config", exist_ok=True)
        dummy_config_content = {
            'model': {
                'name': 'yolov8n.pt', # Standard model for testing
                'path': 'models/yolov8n.pt', # Path where it might be saved or name for download
                'confidence_threshold': 0.3,
                'iou_threshold': 0.45,
                'classes': {'person': 0} # Assuming we are looking for persons with a generic model
            }
        }
        with open("config/config.yaml", 'w') as f:
            yaml.dump(dummy_config_content, f)

    # Create a dummy image for testing
    dummy_image_path = "dummy_test_image.jpg"
    if not os.path.exists(dummy_image_path):
        print(f"Creating dummy image {dummy_image_path} for testing.")
        cv2.imwrite(dummy_image_path, cv2.imread("https://ultralytics.com/images/bus.jpg")) # Use a known image

    if os.path.exists(dummy_image_path):
        print(f"Loading test image: {dummy_image_path}")
        test_frame = cv2.imread(dummy_image_path)
        if test_frame is None:
            print(f"Error: Could not load the dummy image from {dummy_image_path}")
        else:
            print("Initializing YOLOHelmetDetector...")
            try:
                detector = YOLOHelmetDetector(config_path="config/config.yaml")
                print("Detector initialized. Performing detection...")
                detections = detector.detect(test_frame)
                print(f"Detections: {detections}")

                # Draw detections on the frame (optional visualization)
                for det in detections:
                    box = det['box']
                    label = f"{det['class_name']}: {det['confidence']:.2f}"
                    cv2.rectangle(test_frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
                    cv2.putText(test_frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                output_image_path = "dummy_test_image_with_detections.jpg"
                cv2.imwrite(output_image_path, test_frame)
                print(f"Test image with detections saved to: {output_image_path}")

            except RuntimeError as e:
                print(f"RuntimeError during YOLOHelmetDetector test: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during YOLOHelmetDetector test: {e}")
    else:
        print(f"Test image {dummy_image_path} not found. Skipping YOLOHelmetDetector test.")

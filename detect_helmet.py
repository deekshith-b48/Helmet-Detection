import cv2
from src.core.helmet_detector import YOLOHelmetDetector
from src.core.violation_detector import ViolationDetector # Import ViolationDetector
# from src.utils.db_manager import DBManager
# from src.utils.notifier import Notifier
import argparse
import yaml
import os

def load_config(config_path="config/config.yaml"):
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}. Cannot proceed.")
        # Create a minimal default config for basic operation if needed, or exit
        # For now, exiting is safer if the primary config is missing.
        raise FileNotFoundError(f"Configuration file {config_path} not found.")

    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    return config_data

def main(args):
    try:
        config = load_config(args.config_path)
    except FileNotFoundError as e:
        print(e)
        return

    # Initialize components
    try:
        helmet_detector = YOLOHelmetDetector(config_path=args.config_path)
        violation_detector = ViolationDetector(config_path=args.config_path) # Initialize ViolationDetector
    except RuntimeError as e:
        print(f"Failed to initialize detectors: {e}")
        return
    except FileNotFoundError as e: # If config was not found during detector init (though load_config should catch it first)
        print(f"Error during detector initialization (config file problem): {e}")
        return

    # db_manager = DBManager(db_config=config.get('database', {}))
    # notifier = Notifier(notification_config=config.get('notifications', {}))

    if args.video_path:
        cap = cv2.VideoCapture(args.video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {args.video_path}")
            return
    else:
        cap = cv2.VideoCapture(0) # Use webcam
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

    print("Starting detection...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Perform helmet detection
        detections = helmet_detector.detect(frame)

        # --- Placeholder for drawing detections and further processing ---
        # For each detection, draw a bounding box
        # for det in detections:
        #     x1, y1, x2, y2, conf, cls_id = det
        #     label = f"Helmet {conf:.2f}" if cls_id == helmet_class else f"No-Helmet {conf:.2f}"
        #     color = (0, 255, 0) if cls_id == helmet_class else (0, 0, 255)
        #     cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        #     cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # violations = violation_detector.detect_violations(detections, frame)
        # for v in violations:
        #     db_manager.store_violation(v)
        #     if config['notifications']['enabled']:
        #         notifier.send_notification(subject="Helmet Violation Detected", message=str(v), recipient="admin@example.com")
        # --- End Placeholder ---

        cv2.imshow('Helmet Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Detection finished.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Helmet Detection System")
    parser.add_argument('--video_path', type=str, help="Path to the video file. Uses webcam if not specified.")
    # Add more arguments as needed (e.g., config path)

    args = parser.parse_args()
    main(args)

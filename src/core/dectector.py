import cv2
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

class HelmetDetector:
    def __init__(self, model_path: str, conf_thresh: float = 0.5):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.load_model(model_path)
        self.conf_thresh = conf_thresh
        
    def load_model(self, model_path: str) -> torch.nn.Module:
        """Load YOLOv5 model"""
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        model.to(self.device)
        model.eval()
        return model
        
    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for model input"""
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Resize and normalize
        image = cv2.resize(image, (640, 640))
        image = image.transpose((2, 0, 1))
        image = torch.from_numpy(image).float()
        image /= 255.0
        return image.unsqueeze(0).to(self.device)
        
    def detect(self, image: np.ndarray) -> List[Dict]:
        """Detect helmets in image"""
        processed_img = self.preprocess_image(image)
        
        # Inference
        with torch.no_grad():
            predictions = self.model(processed_img)
            
        # Process predictions
        detections = []
        for pred in predictions.pred[0]:
            if pred[4] >= self.conf_thresh:
                x1, y1, x2, y2 = map(int, pred[:4])
                conf = float(pred[4])
                class_id = int(pred[5])
                
                detections.append({
                    'bbox': (x1, y1, x2, y2),
                    'confidence': conf,
                    'class_id': class_id
                })
                
        return detections
        
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw bounding boxes on image"""
        img_copy = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            class_id = det['class_id']
            
            # Draw bbox
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"Helmet: {conf:.2f}"
            cv2.putText(img_copy, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                       
        return img_copy
        
    def process_video(self, video_path: str, output_path: str = None):
        """Process video for helmet detection"""
        cap = cv2.VideoCapture(video_path)
        
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 30.0, 
                                (int(cap.get(3)), int(cap.get(4))))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Detect helmets
            detections = self.detect(frame)
            
            # Draw results
            frame_with_det = self.draw_detections(frame, detections)
            
            if output_path:
                out.write(frame_with_det)
            
            cv2.imshow('Helmet Detection', frame_with_det)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        if output_path:
            out.release()
        cv2.destroyAllWindows()

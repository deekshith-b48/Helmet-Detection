import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path
from typing import List, Tuple, Dict

class YOLOModel:
    """YOLO model wrapper for helmet detection"""
    
    def __init__(self, config: Dict):
        self.model_path = Path(config['MODEL_PATH'])
        self.confidence_threshold = config['CONFIDENCE_THRESHOLD']
        self.nms_threshold = config['NMS_THRESHOLD']
        self.model = self._load_model()
        
    def _load_model(self) -> tf.Graph:
        """Load the YOLO model"""
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(str(self.model_path), 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        return detection_graph
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for model input"""
        blob = cv2.dnn.blobFromImage(
            image, 
            1/255.0, 
            (416, 416), 
            swapRB=True, 
            crop=False
        )
        return blob
        
    def postprocess_detections(
        self, 
        detections: np.ndarray, 
        image_shape: Tuple[int, int]
    ) -> List[Dict]:
        """Process raw detections into structured format"""
        processed_detections = []
        
        for detection in detections:
            confidence = detection[4]
            if confidence > self.confidence_threshold:
                class_id = np.argmax(detection[5:])
                center_x = int(detection[0] * image_shape[1])
                center_y = int(detection[1] * image_shape[0])
                width = int(detection[2] * image_shape[1])
                height = int(detection[3] * image_shape[0])
                
                # Calculate bounding box coordinates
                x = int(center_x - width/2)
                y = int(center_y - height/2)
                
                processed_detections.append({
                    'class_id': class_id,
                    'confidence': float(confidence),
                    'bbox': (x, y, width, height)
                })
                
        return self._apply_nms(processed_detections)
        
    def _apply_nms(self, detections: List[Dict]) -> List[Dict]:
        """Apply Non-Maximum Suppression"""
        if not detections:
            return []
            
        # Extract bounding boxes and scores
        boxes = np.array([d['bbox'] for d in detections])
        scores = np.array([d['confidence'] for d in detections])
        
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            scores.tolist(),
            self.confidence_threshold,
            self.nms_threshold
        )
        
        return [detections[i] for i in indices]
        
    def detect(self, image: np.ndarray) -> List[Dict]:
        """Perform detection on an image"""
        # Preprocess
        blob = self.preprocess_image(image)
        
        with self.model.as_default():
            with tf.Session(graph=self.model) as sess:
                # Get tensors
                image_tensor = self.model.get_tensor_by_name('image_tensor:0')
                boxes = self.model.get_tensor_by_name('detection_boxes:0')
                scores = self.model.get_tensor_by_name('detection_scores:0')
                classes = self.model.get_tensor_by_name('detection_classes:0')
                
                # Run detection
                (boxes, scores, classes) = sess.run(
                    [boxes, scores, classes],
                    feed_dict={image_tensor: np.expand_dims(image, axis=0)}
                )
                
                # Process detections
                detections = self.postprocess_detections(
                    boxes[0],
                    image.shape[:2]
                )
                
                return detections

class DetectionModel:
    """High-level model interface"""
    
    def __init__(self, config: Dict):
        self.helmet_model = YOLOModel(config)
        self.classes = config['CLASSES']
        
    def process_frame(self, frame: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """Process a single frame"""
        # Make copy of frame
        processed_frame = frame.copy()
        
        # Perform detection
        detections = self.helmet_model.detect(processed_frame)
        
        # Classify detections
        classified_detections = self._classify_detections(detections)
        
        return classified_detections, processed_frame
        
    def _classify_detections(self, detections: List[Dict]) -> List[Dict]:
        """Classify detections into specific categories"""
        classified = []
        
        for detection in detections:
            class_name = self.classes[detection['class_id']]
            detection['class_name'] = class_name
            classified.append(detection)
            
        return classified
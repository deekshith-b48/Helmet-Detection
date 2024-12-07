import tensorflow as tf
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ModelLoader:
    """Handles loading and management of detection models"""
    
    def __init__(self, config: Dict):
        self.model_path = Path(config['MODEL_PATH'])
        self.config_path = Path(config.get('CONFIG_PATH', ''))
        self.weights_path = Path(config.get('WEIGHTS_PATH', ''))
        self.detection_graph = None
        self.session = None
        
    def load_frozen_graph(self) -> Optional[tf.Graph]:
        """Load frozen inference graph"""
        try:
            detection_graph = tf.Graph()
            with detection_graph.as_default():
                od_graph_def = tf.GraphDef()
                with tf.gfile.GFile(str(self.model_path), 'rb') as fid:
                    serialized_graph = fid.read()
                    od_graph_def.ParseFromString(serialized_graph)
                    tf.import_graph_def(od_graph_def, name='')
                    
            self.detection_graph = detection_graph
            self.session = tf.Session(graph=detection_graph)
            logger.info("Model loaded successfully")
            return detection_graph
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
            
    def load_yolo_weights(self) -> bool:
        """Load YOLO weights and configuration"""
        try:
            # Load YOLO configuration
            with open(self.config_path, 'r') as f:
                self.net_config = f.read()
                
            # Load weights
            if self.weights_path.exists():
                self.net.load_weights(str(self.weights_path))
                logger.info("YOLO weights loaded successfully")
                return True
            else:
                logger.error("Weights file not found")
                return False
                
        except Exception as e:
            logger.error(f"Error loading YOLO weights: {e}")
            return False
            
    def get_tensors(self) -> Dict:
        """Get input and output tensors"""
        try:
            tensors = {
                'image_tensor': self.detection_graph.get_tensor_by_name('image_tensor:0'),
                'detection_boxes': self.detection_graph.get_tensor_by_name('detection_boxes:0'),
                'detection_scores': self.detection_graph.get_tensor_by_name('detection_scores:0'),
                'detection_classes': self.detection_graph.get_tensor_by_name('detection_classes:0'),
                'num_detections': self.detection_graph.get_tensor_by_name('num_detections:0')
            }
            return tensors
        except Exception as e:
            logger.error(f"Error getting tensors: {e}")
            return {}
            
    def run_inference(self, image: np.ndarray) -> Dict:
        """Run inference on an image"""
        try:
            tensors = self.get_tensors()
            if not tensors:
                return {}
                
            image_expanded = np.expand_dims(image, axis=0)
            
            (boxes, scores, classes, num) = self.session.run(
                [tensors['detection_boxes'],
                 tensors['detection_scores'],
                 tensors['detection_classes'],
                 tensors['num_detections']],
                feed_dict={tensors['image_tensor']: image_expanded})
                
            return {
                'boxes': boxes,
                'scores': scores,
                'classes': classes,
                'num': num
            }
            
        except Exception as e:
            logger.error(f"Error running inference: {e}")
            return {}
            
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.session:
                self.session.close()
            logger.info("Model resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up model resources: {e}")
            
class ModelManager:
    """Manages multiple detection models"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.models = {}
        
    def load_models(self):
        """Load all required models"""
        try:
            # Load helmet detection model
            helmet_model = ModelLoader(self.config['helmet_model'])
            if helmet_model.load_frozen_graph():
                self.models['helmet'] = helmet_model
                
            # Load license plate model
            plate_model = ModelLoader(self.config['plate_model'])
            if plate_model.load_frozen_graph():
                self.models['plate'] = plate_model
                
            return len(self.models) > 0
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
            
    def get_model(self, model_type: str) -> Optional[ModelLoader]:
        """Get specific model by type"""
        return self.models.get(model_type)
        
    def cleanup(self):
        """Clean up all models"""
        for model in self.models.values():
            model.cleanup()
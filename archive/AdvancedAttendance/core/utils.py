import os
import yaml
import cv2
import numpy as np
from loguru import logger
from datetime import datetime
from PyQt5.QtGui import QImage, QPixmap

def load_config(config_path="config/config.yaml"):
    """Load application configuration."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}

def load_camera_config(config_path="config/camera_config.yaml"):
    """Load camera configuration."""
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('cameras', [])
    except Exception as e:
        logger.error(f"Failed to load camera config from {config_path}: {e}")
        return []

def setup_logging(log_dir="logs"):
    """Configure loguru logging."""
    os.makedirs(log_dir, exist_ok=True)
    logger.add(
        os.path.join(log_dir, "app_{time}.log"),
        rotation="500 MB",
        retention="10 days",
        level="INFO"
    )

def cv2_to_qpixmap(cv_img):
    """Convert OpenCV image to QPixmap for PyQt5."""
    if cv_img is None:
        return QPixmap()
    
    height, width, channel = cv_img.shape
    bytes_per_line = 3 * width
    
    # Convert BGR to RGB
    rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    
    q_img = QImage(rgb_img.data, width, height, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(q_img)

def draw_overlays(frame, faces, fps=0):
    """Draw bounding boxes and metadata on frame."""
    if frame is None:
        return None
        
    # Draw FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
    for face in faces:
        bbox = face.get('bbox')
        name = face.get('name', 'Unknown')
        conf = face.get('confidence', 0.0)
        age = face.get('age')
        gender = face.get('gender')
        
        if bbox is not None:
            x1, y1, x2, y2 = map(int, bbox)
            
            # Color based on recognition
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            # Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{name} ({conf:.2f})"
            if age and gender:
                label += f" [{gender}, {age}]"
                
            cv2.rectangle(frame, (x1, y1-25), (x2, y1), color, -1)
            cv2.putText(frame, label, (x1+5, y1-5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
    return frame

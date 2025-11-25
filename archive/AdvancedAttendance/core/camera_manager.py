import cv2
import threading
import time
import queue
from loguru import logger

class CameraThread(threading.Thread):
    def __init__(self, camera_config):
        super().__init__()
        self.config = camera_config
        self.id = camera_config['id']
        self.name = camera_config['name']
        self.source = camera_config['source']
        self.running = False
        self.frame_queue = queue.Queue(maxsize=2)
        self.latest_frame = None
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

    def run(self):
        logger.info(f"Starting camera {self.name} ({self.source})")
        cap = cv2.VideoCapture(self.source)
        
        # Set resolution if possible
        if isinstance(self.source, int):
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.get('width', 640))
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.get('height', 480))
            cap.set(cv2.CAP_PROP_FPS, self.config.get('fps', 30))
            
        self.running = True
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Failed to read frame from {self.name}, retrying...")
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(self.source)
                continue
                
            # Rotation
            rotation = self.config.get('rotation', 0)
            if rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
            # Update FPS
            self.frame_count += 1
            if time.time() - self.start_time > 1:
                self.fps = self.frame_count / (time.time() - self.start_time)
                self.frame_count = 0
                self.start_time = time.time()
                
            # Update queue
            if not self.frame_queue.full():
                self.frame_queue.put(frame)
            
            self.latest_frame = frame
            time.sleep(0.01) # Prevent CPU hogging
            
        cap.release()
        logger.info(f"Stopped camera {self.name}")

    def stop(self):
        self.running = False
        self.join()

    def get_frame(self):
        if not self.frame_queue.empty():
            return self.frame_queue.get()
        return self.latest_frame

class CameraManager:
    def __init__(self, config_list):
        self.cameras = {}
        self.config_list = config_list
        
    def start_all(self):
        for cam_conf in self.config_list:
            if cam_conf.get('enabled', True):
                self.start_camera(cam_conf)
                
    def start_camera(self, cam_conf):
        cam_id = cam_conf['id']
        if cam_id not in self.cameras:
            thread = CameraThread(cam_conf)
            thread.start()
            self.cameras[cam_id] = thread
            
    def stop_camera(self, cam_id):
        if cam_id in self.cameras:
            self.cameras[cam_id].stop()
            del self.cameras[cam_id]
            
    def stop_all(self):
        for cam_id in list(self.cameras.keys()):
            self.stop_camera(cam_id)
            
    def get_active_cameras(self):
        return self.cameras

import sys
import time
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QStatusBar, QTabWidget)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap

from core.utils import load_config, load_camera_config, setup_logging, cv2_to_qpixmap, draw_overlays
from core.database import FaceDatabase
from core.face_detection import FaceDetector
from core.camera_manager import CameraManager
from core.attendance import AttendanceTracker
from core.alert_system import AlertSystem
from loguru import logger

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(str, QImage)

    def __init__(self, camera_manager, detector, tracker, alert_system):
        super().__init__()
        self.camera_manager = camera_manager
        self.detector = detector
        self.tracker = tracker
        self.alert_system = alert_system
        self.running = True

    def run(self):
        while self.running:
            cameras = self.camera_manager.get_active_cameras()
            
            for cam_id, cam_thread in cameras.items():
                frame = cam_thread.get_frame()
                if frame is None:
                    continue
                
                # Face Detection
                faces = self.detector.process_frame(frame)
                
                # Process Attendance & Alerts
                for face in faces:
                    if face['name'] != "Unknown":
                        self.tracker.process_detection(face, cam_id, cam_thread.name)
                        self.alert_system.trigger_alert(face, frame, cam_thread.name)
                
                # Draw Overlays
                display_frame = frame.copy()
                draw_overlays(display_frame, faces, cam_thread.fps)
                
                # Convert to Qt
                qt_img = cv2_to_qpixmap(display_frame).toImage()
                self.change_pixmap_signal.emit(cam_id, qt_img)
            
            self.tracker.check_timeouts()
            time.sleep(0.03)

    def stop(self):
        self.running = False
        self.wait()

from ui.face_manager import FaceManagerDialog
from ui.history_viewer import HistoryViewer
from ui.alert_panel import AlertPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("InsightFace Attendance System")
        self.resize(1200, 800)
        
        # Load Config
        self.config = load_config("config/config.yaml")
        self.cam_config = load_camera_config("config/camera_config.yaml")
        setup_logging(self.config['directories']['logs'])
        
        # Initialize Core Systems
        self.db = FaceDatabase()
        self.detector = FaceDetector(self.config)
        
        # Load known faces
        known_faces = self.db.get_known_faces()
        self.detector.load_known_faces(known_faces)
        
        self.tracker = AttendanceTracker(self.db, self.config)
        self.alert_system = AlertSystem(self.config)
        self.camera_manager = CameraManager(self.cam_config)
        
        # UI Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Monitor Tab
        self.monitor_tab = QWidget()
        self.monitor_layout = QGridLayout(self.monitor_tab)
        self.tabs.addTab(self.monitor_tab, "Monitor")
        
        # History Tab
        self.history_viewer = HistoryViewer(self.db)
        self.tabs.addTab(self.history_viewer, "History")
        
        # Alerts Tab
        self.alert_panel = AlertPanel()
        self.tabs.addTab(self.alert_panel, "Alerts")
        
        # Camera Widgets
        self.camera_labels = {}
        row, col = 0, 0
        for cam in self.cam_config:
            if not cam.get('enabled', True):
                continue
                
            label = QLabel(f"Camera: {cam['name']}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background-color: black; color: white;")
            label.setMinimumSize(400, 300)
            
            self.monitor_layout.addWidget(label, row, col)
            self.camera_labels[cam['id']] = label
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        # Controls
        self.controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start System")
        self.start_btn.clicked.connect(self.start_system)
        self.stop_btn = QPushButton("Stop System")
        self.stop_btn.clicked.connect(self.stop_system)
        self.stop_btn.setEnabled(False)
        
        self.faces_btn = QPushButton("Manage Faces")
        self.faces_btn.clicked.connect(self.open_face_manager)
        
        self.controls_layout.addWidget(self.start_btn)
        self.controls_layout.addWidget(self.stop_btn)
        self.controls_layout.addWidget(self.faces_btn)
        self.layout.addLayout(self.controls_layout)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("System Ready")

    def open_face_manager(self):
        dialog = FaceManagerDialog(self.db, self.detector, self)
        dialog.exec_()

    def start_system(self):
        self.camera_manager.start_all()
        self.alert_system.start()
        
        self.video_thread = VideoThread(
            self.camera_manager, 
            self.detector, 
            self.tracker, 
            self.alert_system
        )
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage("System Running")

    def stop_system(self):
        if hasattr(self, 'video_thread'):
            self.video_thread.stop()
        
        self.camera_manager.stop_all()
        self.alert_system.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("System Stopped")

    def update_image(self, cam_id, qt_img):
        if cam_id in self.camera_labels:
            self.camera_labels[cam_id].setPixmap(QPixmap.fromImage(qt_img).scaled(
                self.camera_labels[cam_id].size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))

    def closeEvent(self, event):
        self.stop_system()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

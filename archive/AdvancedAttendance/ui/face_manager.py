from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QListWidget, 
                             QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import cv2
import numpy as np
import pickle
import os

class FaceEmbeddingThread(QThread):
    finished = pyqtSignal(bool, str, object) # success, message, embedding

    def __init__(self, detector, image_path):
        super().__init__()
        self.detector = detector
        self.image_path = image_path

    def run(self):
        try:
            img = cv2.imread(self.image_path)
            if img is None:
                self.finished.emit(False, "Failed to load image", None)
                return

            # Use the detector to get embedding
            # We need to access the underlying InsightFace app directly or add a method
            # Let's use the process_frame but we need the raw embedding
            # Actually, FaceDetector.process_frame returns embeddings in the result dict
            
            results = self.detector.process_frame(img)
            
            if not results:
                self.finished.emit(False, "No face detected", None)
                return
                
            if len(results) > 1:
                self.finished.emit(False, "Multiple faces detected. Please use an image with a single face.", None)
                return
                
            embedding = results[0]['embedding']
            self.finished.emit(True, "Face processed successfully", embedding)
            
        except Exception as e:
            self.finished.emit(False, str(e), None)

class FaceManagerDialog(QDialog):
    def __init__(self, db, detector, parent=None):
        super().__init__(parent)
        self.db = db
        self.detector = detector
        self.setWindowTitle("Manage Known Faces")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # List
        self.face_list = QListWidget()
        self.refresh_list()
        layout.addWidget(self.face_list)
        
        # Form
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Name")
        form_layout.addWidget(self.name_input)
        
        self.file_btn = QPushButton("Select Image")
        self.file_btn.clicked.connect(self.select_image)
        form_layout.addWidget(self.file_btn)
        
        self.add_btn = QPushButton("Add Face")
        self.add_btn.clicked.connect(self.add_face)
        self.add_btn.setEnabled(False)
        form_layout.addWidget(self.add_btn)
        
        layout.addLayout(form_layout)
        
        # Preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(150)
        self.preview_label.setStyleSheet("border: 1px dashed gray;")
        layout.addWidget(self.preview_label)
        
        # Delete
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_face)
        layout.addWidget(self.delete_btn)
        
        self.selected_image_path = None

    def refresh_list(self):
        self.face_list.clear()
        faces = self.db.get_known_faces()
        for face in faces:
            self.face_list.addItem(face.name)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Face Image", "", "Images (*.jpg *.png *.jpeg)")
        if path:
            self.selected_image_path = path
            pixmap = QPixmap(path).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)
            self.add_btn.setEnabled(True)

    def add_face(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name")
            return
            
        if not self.selected_image_path:
            return

        self.add_btn.setEnabled(False)
        self.file_btn.setEnabled(False)
        self.preview_label.setText("Processing...")
        
        # Process in background
        self.thread = FaceEmbeddingThread(self.detector, self.selected_image_path)
        self.thread.finished.connect(lambda success, msg, emb: self.on_processing_finished(success, msg, emb, name))
        self.thread.start()

    def on_processing_finished(self, success, message, embedding, name):
        self.add_btn.setEnabled(True)
        self.file_btn.setEnabled(True)
        
        if not success:
            QMessageBox.warning(self, "Error", message)
            self.preview_label.setText("Failed")
            return
            
        # Save to DB
        # Serialize embedding
        emb_bytes = pickle.dumps(embedding)
        
        # Save image to data dir
        ext = os.path.splitext(self.selected_image_path)[1]
        new_filename = f"{name.replace(' ', '_')}{ext}"
        new_path = os.path.join("data/known_faces", new_filename)
        
        try:
            import shutil
            shutil.copy(self.selected_image_path, new_path)
            
            if self.db.add_known_face(name, emb_bytes, new_path):
                QMessageBox.information(self, "Success", f"Face added for {name}")
                self.refresh_list()
                self.name_input.clear()
                self.preview_label.clear()
                self.selected_image_path = None
                
                # Reload in detector
                self.detector.load_known_faces(self.db.get_known_faces())
            else:
                QMessageBox.critical(self, "Error", "Database error (Name might already exist)")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_face(self):
        # Implement delete logic here
        pass

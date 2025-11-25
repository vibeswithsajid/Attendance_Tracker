from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QLabel, QListWidgetItem)
from PyQt5.QtGui import QColor

class AlertPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Recent Alerts"))
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
    def add_alert(self, message, level="info"):
        item = QListWidgetItem(message)
        if level == "warning":
            item.setBackground(QColor("#fff3cd"))
        elif level == "error":
            item.setBackground(QColor("#f8d7da"))
        
        self.list_widget.insertItem(0, item)
        
        # Keep only last 50
        if self.list_widget.count() > 50:
            self.list_widget.takeItem(50)

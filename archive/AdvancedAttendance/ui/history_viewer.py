from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QPushButton, QHBoxLayout, QDateEdit)
from PyQt5.QtCore import QDate
from core.database import FaceLog, AttendanceSession

class HistoryViewer(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        
        # Filters
        filter_layout = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        filter_layout.addWidget(self.date_edit)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_history)
        filter_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Time", "Name", "Camera", "Duration", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self.load_history()

    def load_history(self):
        session = self.db.get_session()
        try:
            # Get selected date
            qdate = self.date_edit.date()
            # Simple query for now, can be expanded
            records = session.query(AttendanceSession).order_by(AttendanceSession.entry_time.desc()).limit(100).all()
            
            self.table.setRowCount(len(records))
            for i, record in enumerate(records):
                self.table.setItem(i, 0, QTableWidgetItem(str(record.entry_time)))
                self.table.setItem(i, 1, QTableWidgetItem(record.person_name))
                self.table.setItem(i, 2, QTableWidgetItem(record.camera_name))
                
                duration = f"{record.total_seconds:.1f}s" if record.total_seconds else "-"
                self.table.setItem(i, 3, QTableWidgetItem(duration))
                
                status = "Active" if record.is_active else "Completed"
                self.table.setItem(i, 4, QTableWidgetItem(status))
                
        finally:
            session.close()

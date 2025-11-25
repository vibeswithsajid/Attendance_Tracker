from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, Response
from flask_cors import CORS
import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime, timedelta, time as dt_time
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import threading
import time
import traceback
from functools import wraps
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import pandas as pd

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your-secret-key-change-in-production-12345'  # Change this in production!
CORS(app)

# Hardcoded login credentials
# Login credentials (use environment variables in production)
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@gmail.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///attendance.db', echo=False)
Session = sessionmaker(bind=engine)

# Create uploads directory
os.makedirs('uploads', exist_ok=True)
os.makedirs('known_faces', exist_ok=True)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    usn = Column(String(50), nullable=False, unique=True)  # University Serial Number (unique)
    password = Column(String(255), nullable=True)  # For student login (optional, can use USN)
    face_encodings = Column(String, nullable=False)  # JSON array of multiple face encodings
    image_paths = Column(String)  # JSON array of image paths (3-5 photos)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.now)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)  # Admin who approved

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String(100), nullable=False)
    user_usn = Column(String(50), nullable=False)  # University Serial Number
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    duration_minutes = Column(Float)
    camera_id = Column(String(50), default='door_camera')
    is_late = Column(Integer, default=0)  # 0 = on time, 1 = late
    class_start_time = Column(DateTime, nullable=True)  # For late detection
    date = Column(String(20), nullable=False)  # YYYY-MM-DD for easy querying

class ClassSettings(Base):
    __tablename__ = 'class_settings'
    id = Column(Integer, primary_key=True)
    class_start_time = Column(String(10), nullable=False, default='09:00:00')  # Format: HH:MM:SS
    late_threshold_minutes = Column(Integer, nullable=False, default=10)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ClassSlot(Base):
    __tablename__ = 'class_slots'
    id = Column(Integer, primary_key=True)
    class_name = Column(String(100), nullable=False)
    start_time = Column(String(10), nullable=False)  # Format: HH:MM
    end_time = Column(String(10), nullable=False)  # Format: HH:MM
    day_of_week = Column(String(20), nullable=True)  # Optional: Monday, Tuesday, etc.
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class SlotAttendance(Base):
    __tablename__ = 'slot_attendance'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String(100), nullable=False)
    user_usn = Column(String(50), nullable=False)
    slot_id = Column(Integer, nullable=False)
    slot_name = Column(String(100), nullable=False)
    date = Column(String(20), nullable=False)  # YYYY-MM-DD
    status = Column(String(20), nullable=False)  # 'Present', 'Absent', 'Late'
    entry_time = Column(DateTime, nullable=True)  # When student entered during this slot
    exit_time = Column(DateTime, nullable=True)  # When student exited during this slot
    overlap_minutes = Column(Float, nullable=True)  # Minutes of overlap with slot
    created_at = Column(DateTime, default=datetime.now)

# Create tables and handle migrations
Base.metadata.create_all(engine)

# Handle database migration for existing databases
def migrate_database():
    """Add missing columns to existing database"""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Only run migration if tables already exist (not a fresh database)
        if 'users' in existing_tables or 'attendance' in existing_tables:
            with engine.connect() as conn:
                try:
                    # Migrate users table
                    if 'users' in existing_tables:
                        result = conn.execute(text("PRAGMA table_info(users)"))
                        columns = [row[1] for row in result]
                        
                        # Handle old face_encoding -> face_encodings migration
                        if 'face_encoding' in columns and 'face_encodings' not in columns:
                            print("Migrating: Converting face_encoding to face_encodings...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN face_encodings VARCHAR"))
                            conn.execute(text("""
                                UPDATE users 
                                SET face_encodings = '[' || face_encoding || ']'
                                WHERE face_encoding IS NOT NULL
                            """))
                            conn.commit()
                            print("Migration complete: face_encodings column added")
                        
                        # Add new columns if missing
                        if 'status' not in columns:
                            conn.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'approved'"))
                            conn.commit()
                            print("Migration: Added status column")
                        
                        if 'image_paths' not in columns:
                            conn.execute(text("ALTER TABLE users ADD COLUMN image_paths VARCHAR"))
                            # Migrate old image_path to image_paths array
                            conn.execute(text("""
                                UPDATE users 
                                SET image_paths = '[' || '"' || image_path || '"' || ']'
                                WHERE image_path IS NOT NULL AND image_paths IS NULL
                            """))
                            conn.commit()
                            print("Migration: Added image_paths column")
                    
                    # Migrate attendance table
                    if 'attendance' in existing_tables:
                        result = conn.execute(text("PRAGMA table_info(attendance)"))
                        columns = [row[1] for row in result]
                        
                        if 'date' not in columns:
                            conn.execute(text("ALTER TABLE attendance ADD COLUMN date VARCHAR(20)"))
                            # Populate date from entry_time
                            conn.execute(text("""
                                UPDATE attendance 
                                SET date = strftime('%Y-%m-%d', entry_time)
                                WHERE date IS NULL
                            """))
                            conn.commit()
                            print("Migration: Added date column")
                        
                        if 'is_late' not in columns:
                            conn.execute(text("ALTER TABLE attendance ADD COLUMN is_late INTEGER DEFAULT 0"))
                            conn.commit()
                            print("Migration: Added is_late column")
                        
                        if 'class_start_time' not in columns:
                            conn.execute(text("ALTER TABLE attendance ADD COLUMN class_start_time DATETIME"))
                            conn.commit()
                            print("Migration: Added class_start_time column")
                    
                    # Migrate class_settings table
                    if 'class_settings' not in existing_tables:
                        conn.execute(text("""
                            CREATE TABLE class_settings (
                                id INTEGER PRIMARY KEY,
                                class_start_time TEXT NOT NULL DEFAULT '09:00:00',
                                late_threshold_minutes INTEGER NOT NULL DEFAULT 10,
                                last_updated TEXT
                            )
                        """))
                        # Insert default values
                        conn.execute(text("""
                            INSERT INTO class_settings (class_start_time, late_threshold_minutes, last_updated)
                            VALUES ('09:00:00', 10, datetime('now'))
                        """))
                        conn.commit()
                        print("Migration: Created class_settings table with default values")
                    else:
                        # Check if table is empty and insert default if needed
                        result = conn.execute(text("SELECT COUNT(*) FROM class_settings"))
                        count = result.scalar()
                        if count == 0:
                            conn.execute(text("""
                                INSERT INTO class_settings (class_start_time, late_threshold_minutes, last_updated)
                                VALUES ('09:00:00', 10, datetime('now'))
                            """))
                            conn.commit()
                            print("Migration: Inserted default class settings")
                    
                    # Migrate class_slots table
                    if 'class_slots' not in existing_tables:
                        conn.execute(text("""
                            CREATE TABLE class_slots (
                                id INTEGER PRIMARY KEY,
                                class_name VARCHAR(100) NOT NULL,
                                start_time VARCHAR(10) NOT NULL,
                                end_time VARCHAR(10) NOT NULL,
                                day_of_week VARCHAR(20),
                                created_at TEXT,
                                updated_at TEXT
                            )
                        """))
                        conn.commit()
                        print("Migration: Created class_slots table")
                    
                    # Migrate slot_attendance table
                    if 'slot_attendance' not in existing_tables:
                        conn.execute(text("""
                            CREATE TABLE slot_attendance (
                                id INTEGER PRIMARY KEY,
                                user_id INTEGER NOT NULL,
                                user_name VARCHAR(100) NOT NULL,
                                user_usn VARCHAR(50) NOT NULL,
                                slot_id INTEGER NOT NULL,
                                slot_name VARCHAR(100) NOT NULL,
                                date VARCHAR(20) NOT NULL,
                                status VARCHAR(20) NOT NULL,
                                entry_time TEXT,
                                exit_time TEXT,
                                overlap_minutes REAL,
                                created_at TEXT
                            )
                        """))
                        conn.commit()
                        print("Migration: Created slot_attendance table")
                except Exception as e:
                    print(f"Migration error: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("Fresh database detected - will be created with correct schema")
            # For fresh database, ensure default class settings are inserted
            with engine.connect() as conn:
                try:
                    result = conn.execute(text("SELECT COUNT(*) FROM class_settings"))
                    count = result.scalar()
                    if count == 0:
                        conn.execute(text("""
                            INSERT INTO class_settings (class_start_time, late_threshold_minutes, last_updated)
                            VALUES ('09:00:00', 10, datetime('now'))
                        """))
                        conn.commit()
                        print("Fresh DB: Inserted default class settings")
                except Exception as e:
                    print(f"Error inserting default class settings: {e}")
    except Exception as e:
        print(f"Migration check error: {e}")
        import traceback
        traceback.print_exc()

# Run migration (only if database exists)
migrate_database()

# Global variables for face recognition
known_face_encodings = []  # List of lists (multiple encodings per user)
known_face_names = []
known_face_usns = []
known_face_ids = []
face_recognition_lock = threading.Lock()

# Real-time alerts queue
alerts_queue = []
alerts_lock = threading.Lock()

# Class schedule - will be loaded from database
def get_class_settings():
    """Get class settings from database"""
    session = Session()
    try:
        settings = session.query(ClassSettings).first()
        if settings:
            return {
                'class_start_time': settings.class_start_time,
                'late_threshold_minutes': settings.late_threshold_minutes
            }
        else:
            # Return defaults if no settings found
            return {
                'class_start_time': '09:00:00',
                'late_threshold_minutes': 10
            }
    finally:
        session.close()

# Active sessions tracking (user_id -> {entry_time, last_seen, camera_id})
active_sessions = {}

# Track active camera threads
# Track active camera threads and their latest frames
active_camera_threads = {}
frame_lock = threading.Lock()

def load_known_faces():
    """Load all known faces from database (only approved users)"""
    global known_face_encodings, known_face_names, known_face_usns, known_face_ids
    session = Session()
    try:
        # Only load approved users
        users = session.query(User).filter(User.status == 'approved').all()
        known_face_encodings = []
        known_face_names = []
        known_face_usns = []
        known_face_ids = []
        
        total_encodings = 0
        for user in users:
            # Load multiple face encodings per user
            encodings_list = json.loads(user.face_encodings) if user.face_encodings else []
            
            # Add each encoding with user info
            for encoding in encodings_list:
                known_face_encodings.append(np.array(encoding))
                known_face_names.append(user.name)
                known_face_usns.append(user.usn)
                known_face_ids.append(user.id)
                total_encodings += 1
        
        print(f"Loaded {len(users)} approved users with {total_encodings} total face encodings")
    finally:
        session.close()

def add_alert(alert_type, message, user_name=None, user_usn=None, timestamp=None):
    """Add alert to queue for real-time notifications"""
    global alerts_queue
    with alerts_lock:
        alert = {
            'type': alert_type,  # 'entry', 'exit', 'late'
            'message': message,
            'user_name': user_name,
            'user_usn': user_usn,
            'timestamp': timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        alerts_queue.append(alert)
        # Keep only last 100 alerts
        if len(alerts_queue) > 100:
            alerts_queue.pop(0)

def check_if_late(entry_time):
    """Check if entry is late based on class start time from database"""
    settings = get_class_settings()
    class_start_str = settings['class_start_time']
    late_threshold = settings['late_threshold_minutes']
    
    if not class_start_str:
        return False
    
    # Parse class start time (format: HH:MM:SS or HH:MM)
    try:
        time_parts = class_start_str.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        # Get today's date
        today = entry_time.date()
        class_start = datetime.combine(today, dt_time(hour, minute, second))
        
        # Calculate late limit (class start + threshold)
        late_limit = class_start + timedelta(minutes=late_threshold)
        
        # Check if entry is after late limit
        return entry_time > late_limit
    except Exception as e:
        print(f"Error checking late status: {e}")
        return False

def get_class_slots_for_date(date_str=None):
    """Get all class slots for a given date (or today if not specified)"""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    session = Session()
    try:
        # Get day of week (0=Monday, 6=Sunday)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_of_week = day_names[date_obj.weekday()]
        
        # Get slots for this day of week, or all slots if day_of_week is None
        slots = session.query(ClassSlot).filter(
            (ClassSlot.day_of_week == day_of_week) | (ClassSlot.day_of_week == None)
        ).order_by(ClassSlot.start_time).all()
        
        return slots
    finally:
        session.close()

def calculate_slot_overlap(entry_time, exit_time, slot_start_str, slot_end_str, date_str):
    """Calculate overlap in minutes between entry/exit times and a slot"""
    try:
        # Parse slot times
        slot_start_parts = slot_start_str.split(':')
        slot_end_parts = slot_end_str.split(':')
        slot_start_hour = int(slot_start_parts[0])
        slot_start_min = int(slot_start_parts[1])
        slot_end_hour = int(slot_end_parts[0])
        slot_end_min = int(slot_end_parts[1])
        
        # Create datetime objects for slot
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        slot_start = datetime.combine(date_obj, dt_time(slot_start_hour, slot_start_min))
        slot_end = datetime.combine(date_obj, dt_time(slot_end_hour, slot_end_min))
        
        # If exit_time is None, use current time
        if exit_time is None:
            exit_time = datetime.now()
        
        # Calculate overlap
        overlap_start = max(entry_time, slot_start)
        overlap_end = min(exit_time, slot_end)
        
        if overlap_start < overlap_end:
            overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
            return overlap_minutes, overlap_start, overlap_end
        else:
            return 0, None, None
    except Exception as e:
        print(f"Error calculating slot overlap: {e}")
        return 0, None, None

def process_slot_attendance(user_id, user_name, user_usn, entry_time, exit_time, date_str):
    """Process attendance for all slots based on entry/exit times"""
    session = Session()
    try:
        slots = get_class_slots_for_date(date_str)
        
        for slot in slots:
            overlap_minutes, overlap_start, overlap_end = calculate_slot_overlap(
                entry_time, exit_time, slot.start_time, slot.end_time, date_str
            )
            
            # If overlap is at least 1 minute, mark as present
            if overlap_minutes >= 1:
                # Check if entry is after slot start (late)
                slot_start_parts = slot.start_time.split(':')
                slot_start_hour = int(slot_start_parts[0])
                slot_start_min = int(slot_start_parts[1])
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                slot_start_dt = datetime.combine(date_obj, dt_time(slot_start_hour, slot_start_min))
                
                # Check if already exists
                existing = session.query(SlotAttendance).filter(
                    SlotAttendance.user_id == user_id,
                    SlotAttendance.slot_id == slot.id,
                    SlotAttendance.date == date_str
                ).first()
                
                if existing:
                    # Update existing record
                    existing.status = 'Late' if entry_time > slot_start_dt else 'Present'
                    existing.entry_time = overlap_start if overlap_start else entry_time
                    existing.exit_time = overlap_end if overlap_end else exit_time
                    existing.overlap_minutes = overlap_minutes
                else:
                    # Create new record
                    status = 'Late' if entry_time > slot_start_dt else 'Present'
                    slot_attendance = SlotAttendance(
                        user_id=user_id,
                        user_name=user_name,
                        user_usn=user_usn,
                        slot_id=slot.id,
                        slot_name=slot.class_name,
                        date=date_str,
                        status=status,
                        entry_time=overlap_start if overlap_start else entry_time,
                        exit_time=overlap_end if overlap_end else exit_time,
                        overlap_minutes=overlap_minutes
                    )
                    session.add(slot_attendance)
            else:
                # No overlap - check if we need to mark as absent
                # Only mark absent if slot has already started and ended
                slot_start_parts = slot.start_time.split(':')
                slot_end_parts = slot.end_time.split(':')
                slot_start_hour = int(slot_start_parts[0])
                slot_start_min = int(slot_start_parts[1])
                slot_end_hour = int(slot_end_parts[0])
                slot_end_min = int(slot_end_parts[1])
                
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                slot_start_dt = datetime.combine(date_obj, dt_time(slot_start_hour, slot_start_min))
                slot_end_dt = datetime.combine(date_obj, dt_time(slot_end_hour, slot_end_min))
                
                # Only mark absent if slot has ended and no attendance record exists
                current_time = datetime.now()
                if current_time > slot_end_dt:
                    existing = session.query(SlotAttendance).filter(
                        SlotAttendance.user_id == user_id,
                        SlotAttendance.slot_id == slot.id,
                        SlotAttendance.date == date_str
                    ).first()
                    
                    if not existing:
                        slot_attendance = SlotAttendance(
                            user_id=user_id,
                            user_name=user_name,
                            user_usn=user_usn,
                            slot_id=slot.id,
                            slot_name=slot.class_name,
                            date=date_str,
                            status='Absent',
                            entry_time=None,
                            exit_time=None,
                            overlap_minutes=0
                        )
                        session.add(slot_attendance)
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error processing slot attendance: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def process_attendance(user_id, user_name, user_usn, camera_id, is_entry=True):
    """Process attendance entry/exit for single door system"""
    current_time = datetime.now()
    today_str = current_time.strftime('%Y-%m-%d')
    
    with face_recognition_lock:
        session = Session()
        try:
            if is_entry:
                # Entry detection
                if user_id in active_sessions:
                    # Already inside - just update last seen
                    active_sessions[user_id]['last_seen'] = current_time
                else:
                    # New entry
                    # Check if there's an incomplete session today
                    existing_entry = session.query(Attendance).filter(
                        Attendance.user_id == user_id,
                        Attendance.date == today_str,
                        Attendance.exit_time == None
                    ).first()
                    
                    if existing_entry:
                        # Resume existing session
                        active_sessions[user_id] = {
                            'entry_time': existing_entry.entry_time,
                            'last_seen': current_time,
                            'camera_id': camera_id,
                            'user_name': user_name,
                            'user_usn': user_usn
                        }
                    else:
                        # Brand new entry
                        is_late = check_if_late(current_time)
                        settings = get_class_settings()
                        class_start_str = settings['class_start_time']
                        
                        # Store class start time as datetime for this record
                        class_start_dt = None
                        if class_start_str:
                            try:
                                time_parts = class_start_str.split(':')
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                second = int(time_parts[2]) if len(time_parts) > 2 else 0
                                today = current_time.date()
                                class_start_dt = datetime.combine(today, dt_time(hour, minute, second))
                            except:
                                pass
                        
                        active_sessions[user_id] = {
                            'entry_time': current_time,
                            'last_seen': current_time,
                            'camera_id': camera_id,
                            'user_name': user_name,
                            'user_usn': user_usn
                        }
                        
                        attendance = Attendance(
                            user_id=user_id,
                            user_name=user_name,
                            user_usn=user_usn,
                            entry_time=current_time,
                            camera_id=camera_id,
                            date=today_str,
                            is_late=1 if is_late else 0,
                            class_start_time=class_start_dt
                        )
                        session.add(attendance)
                        session.commit()
                        
                        # Process slot-based attendance (with None exit_time for now)
                        process_slot_attendance(user_id, user_name, user_usn, current_time, None, today_str)
                        
                        # Add alert
                        if is_late:
                            message = f"⚠️ {user_name} ({user_usn}) entered LATE at {current_time.strftime('%H:%M:%S')}"
                            add_alert('late', message, user_name, user_usn, current_time)
                        else:
                            message = f"✅ {user_name} ({user_usn}) entered at {current_time.strftime('%H:%M:%S')}"
                            add_alert('entry', message, user_name, user_usn, current_time)
                        
                        print(f"✓ Entry recorded: {user_name} (USN: {user_usn}) at {current_time.strftime('%Y-%m-%d %H:%M:%S')} {'[LATE]' if is_late else ''}")
            else:
                # Exit detection
                if user_id in active_sessions:
                    entry_time = active_sessions[user_id]['entry_time']
                    
                    # Find the attendance record
                    attendance = session.query(Attendance).filter(
                        Attendance.user_id == user_id,
                        Attendance.entry_time == entry_time,
                        Attendance.exit_time == None,
                        Attendance.date == today_str
                    ).first()
                    
                    if attendance:
                        exit_time = current_time
                        duration = (exit_time - entry_time).total_seconds() / 60
                        
                        attendance.exit_time = exit_time
                        attendance.duration_minutes = round(duration, 2)
                        session.commit()
                        
                        # Process slot-based attendance with exit time
                        process_slot_attendance(user_id, user_name, user_usn, entry_time, exit_time, today_str)
                        
                        # Add exit alert
                        message = f"🚪 {user_name} ({user_usn}) exited at {exit_time.strftime('%H:%M:%S')} (Duration: {duration:.1f} min)"
                        add_alert('exit', message, user_name, user_usn, exit_time)
                        
                        print(f"✓ Exit recorded: {user_name} - Duration: {duration:.2f} minutes")
                    
                    # Remove from active sessions
                    del active_sessions[user_id]
        except Exception as e:
            session.rollback()
            print(f"✗ ERROR processing attendance for {user_name}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()

def check_exits():
    """Check for users who haven't been seen recently and mark them as exited"""
    global active_sessions
    with face_recognition_lock:
        if not active_sessions:
            return
        
        session = Session()
        try:
            current_time = datetime.now()
            users_to_remove = []
            
            for user_id, session_data in list(active_sessions.items()):
                time_since_last_seen = (current_time - session_data['last_seen']).total_seconds()
                
                # If user hasn't been seen for 30 seconds, mark as exited
                if time_since_last_seen > 30:
                    entry_time = session_data['entry_time']
                    exit_time = session_data['last_seen']
                    duration = (exit_time - entry_time).total_seconds() / 60  # in minutes
                    
                    # Update attendance record - find the most recent entry without exit
                    today_str = current_time.strftime('%Y-%m-%d')
                    attendance = session.query(Attendance).filter(
                        Attendance.user_id == user_id,
                        Attendance.entry_time == entry_time,
                        Attendance.exit_time == None,
                        Attendance.date == today_str
                    ).first()
                    
                    if attendance:
                        attendance.exit_time = exit_time
                        attendance.duration_minutes = round(duration, 2)
                        session.commit()
                        user_name = session_data.get('user_name', 'Unknown')
                        user_usn = session_data.get('user_usn', 'N/A')
                        
                        # Process slot-based attendance with exit time
                        process_slot_attendance(user_id, user_name, user_usn, entry_time, exit_time, today_str)
                        
                        print(f"✓ Exit recorded: {user_name} - Duration: {duration:.2f} minutes")
                    else:
                        print(f"⚠ Warning: Could not find attendance record for user_id {user_id} with entry_time {entry_time}")
                    
                    users_to_remove.append(user_id)
            
            for user_id in users_to_remove:
                if user_id in active_sessions:
                    del active_sessions[user_id]
        except Exception as e:
            session.rollback()
            print(f"✗ ERROR in check_exits: {e}")
            import traceback
            traceback.print_exc()
        finally:
            session.close()

def process_camera_feed(camera_id, camera_url):
    """Process video feed from a camera"""
    print(f"Starting camera feed: {camera_id} from {camera_url}")
    print(f"Known faces loaded: {len(known_face_encodings)}")
    
    cap = cv2.VideoCapture(camera_url)
    
    # Check if camera opened successfully
    if not cap.isOpened():
        error_msg = f"Error: Could not open camera {camera_id} at {camera_url}"
        print(error_msg)
        if camera_id in active_camera_threads:
            del active_camera_threads[camera_id]
        return
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    process_this_frame = True
    frame_count = 0
    
    # Variables to hold results for display
    face_locations = []
    face_names = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"Warning: Could not read frame from camera {camera_id}")
            time.sleep(1)
            # Try to reopen camera
            cap.release()
            cap = cv2.VideoCapture(camera_url)
            if not cap.isOpened():
                print(f"Error: Could not reopen camera {camera_id}")
                break
            continue
        
        frame_count += 1
        
        # Resize frame for faster processing (1/4 size)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Process every other frame to reduce CPU usage
        if process_this_frame:
            try:
                # Find faces and encodings
                face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                
                # Debug: Log face detection
                if len(face_encodings) > 0:
                    if frame_count % 30 == 0:  # Log every 30 frames
                        print(f"Camera {camera_id}: Detected {len(face_encodings)} face(s) in frame {frame_count}")
                
                # Log when faces are detected but not recognized
                if len(face_encodings) > 0:
                    if len(known_face_encodings) == 0:
                        face_names = ["Unknown"] * len(face_encodings)
                    else:
                        # Process ALL faces detected in the frame (multi-face support)
                        recognized_in_frame = set()  # Track recognized users in this frame to avoid duplicates
                        
                        for face_encoding in face_encodings:
                            # Compare faces with lower tolerance for better accuracy
                            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                            
                            name = "Unknown"
                            
                            if True in matches:
                                best_match_index = np.argmin(face_distances)
                                # Only accept if distance is below threshold
                                if matches[best_match_index] and face_distances[best_match_index] < 0.5:
                                    user_id = known_face_ids[best_match_index]
                                    user_name = known_face_names[best_match_index]
                                    name = user_name
                                    
                                    # Get USN from known_face_usns array, or fetch from database if missing
                                    if best_match_index < len(known_face_usns):
                                        user_usn = known_face_usns[best_match_index] or ''
                                    else:
                                        user_usn = ''
                                    
                                    # If USN is empty, try to get it from database
                                    if not user_usn or user_usn == 'N/A':
                                        session_temp = Session()
                                        try:
                                            user = session_temp.query(User).filter(User.id == user_id).first()
                                            if user and user.usn:
                                                user_usn = user.usn
                                                # Update the known_face_usns array
                                                if best_match_index < len(known_face_usns):
                                                    known_face_usns[best_match_index] = user_usn
                                        finally:
                                            session_temp.close()
                                    
                                    # Only process if not already recognized in this frame
                                    if user_id not in recognized_in_frame:
                                        # For single door: detect entry (face appears)
                                        process_attendance(user_id, user_name, user_usn or '', camera_id, is_entry=True)
                                        recognized_in_frame.add(user_id)
                                        print(f"✓ Face recognized: {user_name} (USN: {user_usn or 'N/A'}, ID: {user_id}) on camera {camera_id}")
                            
                            face_names.append(name)
                            
            except Exception as e:
                print(f"Error processing frame from camera {camera_id}: {e}")
                import traceback
                traceback.print_exc()
        
        process_this_frame = not process_this_frame
        
        # Draw results on the frame for streaming
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.75, (255, 255, 255), 1)
            
        # Store the latest frame for streaming
        with frame_lock:
            if camera_id in active_camera_threads:
                # Encode frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    active_camera_threads[camera_id]['latest_frame'] = buffer.tobytes()
        
        time.sleep(0.033)  # ~30 FPS processing
    
    cap.release()
    with frame_lock:
        if camera_id in active_camera_threads:
            del active_camera_threads[camera_id]
    print(f"Camera feed {camera_id} stopped")

# Background thread to check for exits
def exit_checker_thread():
    while True:
        check_exits()
        time.sleep(10)  # Check every 10 seconds

# Start exit checker thread
exit_thread = threading.Thread(target=exit_checker_thread, daemon=True)
exit_thread.start()

# Load known faces on startup
load_known_faces()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['email'] = email
            return jsonify({'success': True, 'message': 'Login successful'}), 200
        else:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
    
    # GET request - show login page
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/')
def index():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/student/register', methods=['GET'])
def student_register_page():
    """Student registration page"""
    return render_template('register.html')

@app.route('/student/login', methods=['GET'])
def student_login_page():
    """Student login page"""
    return render_template('student_login.html')

@app.route('/student/dashboard', methods=['GET'])
def student_dashboard_page():
    """Student dashboard page"""
    return render_template('student_dashboard.html')

@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    """Add a new user with face image (Admin only)"""
    if 'image' not in request.files or 'name' not in request.form or 'usn' not in request.form:
        return jsonify({'error': 'Missing image, name, or USN'}), 400
    
    name = request.form['name']
    usn = request.form['usn'].strip().upper()  # Convert to uppercase and strip whitespace
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not usn:
        return jsonify({'error': 'USN cannot be empty'}), 400
    
    # Save uploaded image
    filename = f"{int(time.time())}_{file.filename}"
    filepath = os.path.join('uploads', filename)
    file.save(filepath)
    
    # Load and encode face
    try:
        image = face_recognition.load_image_file(filepath)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            os.remove(filepath)
            return jsonify({'error': 'No face detected in image. Please ensure a clear face is visible and well-lit.'}), 400
        
        # Use the first face if multiple faces detected
        if len(face_encodings) > 1:
            print(f"Warning: Multiple faces detected in image for user {name}. Using the first face.")
        
        face_encoding = face_encodings[0]
    except Exception as e:
        os.remove(filepath)
        print(f"Error processing face image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error processing image: {str(e)}'}), 400
    
    # Save to database
    db_session = Session()
    try:
        # Check if USN already exists
        existing_user = db_session.query(User).filter(User.usn == usn).first()
        if existing_user:
            os.remove(filepath)
            return jsonify({'error': f'USN {usn} already exists for user "{existing_user.name}"'}), 400
        
        # Get admin email from Flask session (not SQLAlchemy session)
        admin_email = session.get('email', 'admin@gmail.com')
        
        user = User(
            name=name,
            usn=usn,
            face_encodings=json.dumps([face_encoding.tolist()]),
            image_paths=json.dumps([filepath]),
            status='approved',
            approved_at=datetime.now(),
            approved_by=admin_email
        )
        db_session.add(user)
        db_session.commit()
        
        # Reload known faces
        load_known_faces()
        
        print(f"User added successfully: {name} ({usn})")
        return jsonify({
            'id': user.id,
            'name': user.name,
            'usn': user.usn,
            'message': 'User added successfully'
        }), 201
    except Exception as e:
        db_session.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        print(f"Error adding user to database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        db_session.close()

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Get all users (Admin only)"""
    session = Session()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        return jsonify([{
            'id': user.id,
            'name': user.name,
            'usn': user.usn,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'image_paths': json.loads(user.image_paths) if user.image_paths else [],
            'status': user.status,
            'approved_at': user.approved_at.strftime('%Y-%m-%d %H:%M:%S') if user.approved_at else None
        } for user in users])
    finally:
        session.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete the image files if they exist
        if user.image_paths:
            image_paths = json.loads(user.image_paths) if user.image_paths else []
            for path in image_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        print(f"Warning: Could not delete image file {path}: {e}")
        
        # Delete user
        user_name = user.name
        session.delete(user)
        session.commit()
        
        # Reload known faces
        load_known_faces()
        
        print(f"User deleted: {user_name} (ID: {user_id})")
        return jsonify({
            'message': f'User "{user_name}" deleted successfully',
            'id': user_id
        }), 200
    finally:
        session.close()

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """Get attendance records"""
    session = Session()
    try:
        # Get all attendance records, ordered by most recent first
        records = session.query(Attendance).order_by(Attendance.entry_time.desc()).limit(200).all()
        
        result = []
        for record in records:
            # Get USN from attendance record, or fetch from user if missing
            usn = getattr(record, 'user_usn', '') or ''
            if not usn or usn == 'N/A':
                # Try to get USN from user table
                user = session.query(User).filter(User.id == record.user_id).first()
                if user and user.usn:
                    usn = user.usn
                    # Update the attendance record with USN for future queries
                    try:
                        record.user_usn = usn
                        session.commit()
                    except:
                        session.rollback()
            
            # Format duration
            if record.duration_minutes:
                if record.duration_minutes < 60:
                    duration_str = f"{record.duration_minutes:.1f} min"
                else:
                    hours = int(record.duration_minutes // 60)
                    minutes = int(record.duration_minutes % 60)
                    duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = "In progress"
            
            result.append({
                'id': record.id,
                'name': record.user_name,
                'usn': usn or 'N/A',
                'date': getattr(record, 'date', record.entry_time.strftime('%Y-%m-%d')),
                'entry': record.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                'exit': record.exit_time.strftime('%Y-%m-%d %H:%M:%S') if record.exit_time else 'N/A',
                'duration': duration_str,
                'is_late': bool(getattr(record, 'is_late', 0))
            })
        
        print(f"Returning {len(result)} attendance records")
        return jsonify(result)
    except Exception as e:
        print(f"Error getting attendance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/active-sessions', methods=['GET'])
def get_active_sessions():
    """Get currently active sessions"""
    with face_recognition_lock:
        sessions = []
        current_time = datetime.now()
        for user_id, session_data in active_sessions.items():
            time_present = (current_time - session_data['entry_time']).total_seconds() / 60
            sessions.append({
                'user_id': user_id,
                'user_name': session_data.get('user_name', 'Unknown'),
                'user_usn': session_data.get('user_usn', 'N/A'),
                'entry_time': session_data['entry_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'time_present': f"{time_present:.1f} min",
                'camera_id': session_data.get('camera_id', 'Unknown')
            })
        return jsonify(sessions)

@app.route('/api/cameras', methods=['GET', 'POST'])
@login_required
def cameras():
    """Get list of active cameras or add a new camera"""
    if request.method == 'GET':
        # Return list of active cameras
        cameras_list = []
        with frame_lock:
            for camera_id, camera_data in active_camera_threads.items():
                cameras_list.append({
                    'camera_id': camera_id,
                    'camera_url': str(camera_data.get('camera_url', 'N/A')),
                    'started_at': camera_data.get('started_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S') if isinstance(camera_data.get('started_at'), datetime) else str(camera_data.get('started_at', 'N/A')),
                    'status': 'running'
                })
        return jsonify(cameras_list), 200
    
    # POST - Add a new camera
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    camera_id = data.get('camera_id')
    camera_url = data.get('camera_url', 0)  # Default to webcam 0
    
    if not camera_id:
        return jsonify({'error': 'Camera ID is required'}), 400
    
    # Check if camera already running
    with frame_lock:
        if camera_id in active_camera_threads:
            return jsonify({'error': f'Camera {camera_id} is already running'}), 400
    
    # Check if we have any registered users (warning only, not blocking)
    if len(known_face_encodings) == 0:
        print("Warning: Starting camera without registered users. Face recognition will not work.")
    
    # Convert camera_url to int if it's a number string
    try:
        if isinstance(camera_url, str) and camera_url.isdigit():
            camera_url = int(camera_url)
    except:
        pass  # Keep as string if it's an RTSP URL
    
    # Start processing thread for this camera
    thread = threading.Thread(
        target=process_camera_feed,
        args=(camera_id, camera_url),
        daemon=True
    )
    thread.start()
    
    with frame_lock:
        active_camera_threads[camera_id] = {
            'thread': thread,
            'camera_url': camera_url,
            'started_at': datetime.now(),
            'latest_frame': None
        }
    
    print(f"Camera {camera_id} thread started. Total known faces: {len(known_face_encodings)}")
    return jsonify({
        'message': f'Camera {camera_id} started successfully',
        'camera_id': camera_id,
        'known_faces_count': len(known_face_encodings)
    }), 200

def generate_frames(camera_id):
    """Generator function for video streaming"""
    while True:
        frame_data = None
        with frame_lock:
            if camera_id in active_camera_threads:
                frame_data = active_camera_threads[camera_id].get('latest_frame')
        
        if frame_data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        else:
            # If no frame available yet or camera stopped, send a placeholder or wait
            time.sleep(0.1)
            
        time.sleep(0.033)  # Limit to ~30 FPS

@app.route('/api/video_feed/<camera_id>')
@login_required
def video_feed(camera_id):
    """Video streaming route"""
    with frame_lock:
        if camera_id not in active_camera_threads:
            return "Camera not active", 404
    return Response(generate_frames(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    session = Session()
    try:
        user_count = session.query(User).count()
        attendance_count = session.query(Attendance).count()
        active_count = len(active_sessions)
        camera_count = len(active_camera_threads)
        
        # Get recent attendance records count
        recent_attendance = session.query(Attendance).filter(
            Attendance.entry_time >= datetime.now() - timedelta(hours=24)
        ).count()
        
        return jsonify({
            'users_registered': user_count,
            'known_faces_loaded': len(known_face_encodings),
            'attendance_records': attendance_count,
            'recent_attendance_24h': recent_attendance,
            'active_sessions': active_count,
            'active_cameras': camera_count,
            'camera_list': list(active_camera_threads.keys())
        })
    finally:
        session.close()

@app.route('/api/test-db', methods=['GET'])
def test_database():
    """Test database connectivity and structure"""
    session = Session()
    try:
        from sqlalchemy import text, inspect
        
        # Test basic connectivity
        result = session.execute(text("SELECT 1")).scalar()
        
        # Check table structure
        inspector = inspect(engine)
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        attendance_columns = [col['name'] for col in inspector.get_columns('attendance')]
        
        # Test queries
        user_count = session.query(User).count()
        attendance_count = session.query(Attendance).count()
        
        # Get sample records
        sample_attendance = session.query(Attendance).order_by(Attendance.entry_time.desc()).limit(5).all()
        sample_records = [{
            'id': r.id,
            'user_name': r.user_name,
            'entry_time': r.entry_time.isoformat() if r.entry_time else None,
            'has_usn': hasattr(r, 'user_usn')
        } for r in sample_attendance]
        
        return jsonify({
            'status': 'OK',
            'database_connected': result == 1,
            'users_table_columns': users_columns,
            'attendance_table_columns': attendance_columns,
            'user_count': user_count,
            'attendance_count': attendance_count,
            'sample_records': sample_records,
            'has_usn_column': 'usn' in users_columns,
            'has_user_usn_column': 'user_usn' in attendance_columns
        })
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'error': str(e),
            'traceback': str(traceback.format_exc())
        }), 500
    finally:
        session.close()

# ==================== NEW API ENDPOINTS FOR COMPLETE SYSTEM ====================

@app.route('/api/students/register', methods=['POST'])
def register_student():
    """Student registration with multiple face photos (requires approval)"""
    if 'name' not in request.form or 'usn' not in request.form:
        return jsonify({'error': 'Missing name or USN'}), 400
    
    name = request.form['name']
    usn = request.form['usn'].strip().upper()
    password = request.form.get('password', '') or request.form.get('dob', '')  # Support both 'password' and 'dob' fields
    
    if not usn:
        return jsonify({'error': 'USN cannot be empty'}), 400
    
    # Get multiple images (3-5 photos)
    images = request.files.getlist('images')
    if len(images) < 3:
        return jsonify({'error': 'Please upload at least 3 face photos'}), 400
    if len(images) > 5:
        return jsonify({'error': 'Maximum 5 photos allowed'}), 400
    
    face_encodings_list = []
    image_paths = []
    
    # Process each image
    for idx, file in enumerate(images):
        if file.filename == '':
            continue
        
        filename = f"{int(time.time())}_{idx}_{file.filename}"
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            image = face_recognition.load_image_file(filepath)
            encodings = face_recognition.face_encodings(image)
            
            if len(encodings) == 0:
                os.remove(filepath)
                return jsonify({'error': f'No face detected in photo {idx+1}'}), 400
            
            face_encodings_list.append(encodings[0].tolist())
            image_paths.append(filepath)
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': f'Error processing photo {idx+1}: {str(e)}'}), 400
    
    if len(face_encodings_list) < 3:
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        return jsonify({'error': 'At least 3 valid face photos required'}), 400
    
    session = Session()
    try:
        existing_user = session.query(User).filter(User.usn == usn).first()
        if existing_user:
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
            return jsonify({'error': f'USN {usn} already exists'}), 400
        
        user = User(
            name=name,
            usn=usn,
            password=password if password else None,
            face_encodings=json.dumps(face_encodings_list),
            image_paths=json.dumps(image_paths),
            status='pending'
        )
        session.add(user)
        session.commit()
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'usn': user.usn,
            'status': user.status,
            'message': 'Registration submitted. Waiting for admin approval.'
        }), 201
    finally:
        session.close()

@app.route('/api/students/login', methods=['POST'])
def student_login():
    """Student login using USN and DOB (password)"""
    data = request.get_json()
    usn = data.get('usn', '').strip().upper()
    password = data.get('password', '')
    
    if not usn:
        return jsonify({'error': 'USN is required'}), 400
    
    session = Session()
    try:
        user = session.query(User).filter(User.usn == usn).first()
        if not user:
            return jsonify({'error': 'Invalid USN'}), 401
        
        if user.password and user.password != password:
            return jsonify({'error': 'Invalid password (DOB)'}), 401
        
        # Check if student is approved
        if user.status != 'approved':
            return jsonify({
                'error': 'Your registration is pending approval. Please wait for admin approval.',
                'status': user.status
            }), 403
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'usn': user.usn,
            'status': user.status
        }), 200
    finally:
        session.close()

@app.route('/api/students/<usn>/attendance', methods=['GET'])
def get_student_attendance(usn):
    """Get attendance history for a student"""
    usn = usn.upper()
    date_filter = request.args.get('date')  # Optional: YYYY-MM-DD
    
    session = Session()
    try:
        user = session.query(User).filter(User.usn == usn).first()
        if not user:
            return jsonify({'error': 'Student not found'}), 404
        
        query = session.query(Attendance).filter(Attendance.user_id == user.id)
        if date_filter:
            query = query.filter(Attendance.date == date_filter)
        else:
            # Default to today
            today = datetime.now().strftime('%Y-%m-%d')
            query = query.filter(Attendance.date == today)
        
        records = query.order_by(Attendance.entry_time.desc()).all()
        
        return jsonify([{
            'id': r.id,
            'date': r.date,
            'entry_time': r.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'exit_time': r.exit_time.strftime('%Y-%m-%d %H:%M:%S') if r.exit_time else None,
            'duration_minutes': r.duration_minutes,
            'is_late': bool(r.is_late)
        } for r in records]), 200
    finally:
        session.close()

@app.route('/api/students/<usn>/profile', methods=['GET', 'PUT'])
def student_profile(usn):
    """Get or update student profile"""
    usn = usn.upper()
    session = Session()
    try:
        user = session.query(User).filter(User.usn == usn).first()
        if not user:
            return jsonify({'error': 'Student not found'}), 404
        
        if request.method == 'GET':
            return jsonify({
                'id': user.id,
                'name': user.name,
                'usn': user.usn,
                'status': user.status,
                'image_paths': json.loads(user.image_paths) if user.image_paths else []
            }), 200
        else:
            # Update profile photos
            images = request.files.getlist('images')
            if len(images) < 3:
                return jsonify({'error': 'Please upload at least 3 face photos'}), 400
            
            face_encodings_list = []
            image_paths = []
            
            for idx, file in enumerate(images):
                if file.filename == '':
                    continue
                
                filename = f"{int(time.time())}_{idx}_{file.filename}"
                filepath = os.path.join('uploads', filename)
                file.save(filepath)
                
                try:
                    image = face_recognition.load_image_file(filepath)
                    encodings = face_recognition.face_encodings(image)
                    if len(encodings) > 0:
                        face_encodings_list.append(encodings[0].tolist())
                        image_paths.append(filepath)
                except:
                    os.remove(filepath)
            
            if len(face_encodings_list) >= 3:
                # Delete old images
                old_paths = json.loads(user.image_paths) if user.image_paths else []
                for path in old_paths:
                    if os.path.exists(path):
                        os.remove(path)
                
                user.face_encodings = json.dumps(face_encodings_list)
                user.image_paths = json.dumps(image_paths)
                session.commit()
                
                if user.status == 'approved':
                    load_known_faces()
                
                return jsonify({'message': 'Profile updated successfully'}), 200
            else:
                return jsonify({'error': 'At least 3 valid face photos required'}), 400
    finally:
        session.close()

@app.route('/api/admin/approvals', methods=['GET'])
@login_required
def get_pending_approvals():
    """Get all pending student registrations"""
    session = Session()
    try:
        pending = session.query(User).filter(User.status == 'pending').all()
        return jsonify([{
            'id': u.id,
            'name': u.name,
            'usn': u.usn,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'image_paths': json.loads(u.image_paths) if u.image_paths else []
        } for u in pending]), 200
    finally:
        session.close()

@app.route('/api/admin/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_student(user_id):
    """Approve a student registration"""
    db_session = Session()
    try:
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get admin email from Flask session (not SQLAlchemy session)
        admin_email = session.get('email', 'admin@gmail.com')
        
        user.status = 'approved'
        user.approved_at = datetime.now()
        user.approved_by = admin_email
        db_session.commit()
        
        load_known_faces()
        
        return jsonify({'message': f'Student {user.name} approved successfully'}), 200
    finally:
        db_session.close()

@app.route('/api/admin/reject/<int:user_id>', methods=['POST'])
@login_required
def reject_student(user_id):
    """Reject a student registration"""
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete uploaded images
        image_paths = json.loads(user.image_paths) if user.image_paths else []
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        
        user.status = 'rejected'
        session.commit()
        
        return jsonify({'message': f'Student {user.name} rejected'}), 200
    finally:
        session.close()

@app.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Get real-time alerts"""
    global alerts_queue
    with alerts_lock:
        alerts = list(alerts_queue[-20:])  # Last 20 alerts
        return jsonify(alerts), 200

@app.route('/api/alerts/clear', methods=['POST'])
@login_required
def clear_alerts():
    """Clear alerts queue"""
    global alerts_queue
    with alerts_lock:
        alerts_queue = []
        return jsonify({'message': 'Alerts cleared'}), 200

@app.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    """Get attendance analytics (includes slot-based stats)"""
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    session = Session()
    try:
        # Total students
        total_students = session.query(User).filter(User.status == 'approved').count()
        
        # Today's attendance (legacy - entry/exit based)
        today_records = session.query(Attendance).filter(Attendance.date == date_filter).all()
        present_today = len(set(r.user_id for r in today_records))
        attendance_percent = (present_today / total_students * 100) if total_students > 0 else 0
        
        # Late students (legacy)
        late_count = len([r for r in today_records if r.is_late == 1])
        
        # Average time spent (legacy)
        completed = [r for r in today_records if r.duration_minutes]
        avg_duration = sum(r.duration_minutes for r in completed) / len(completed) if completed else 0
        
        # Currently inside
        currently_inside = len(active_sessions)
        
        # Slot-based statistics
        slots = get_class_slots_for_date(date_filter)
        slot_attendance = session.query(SlotAttendance).filter(
            SlotAttendance.date == date_filter
        ).all()
        
        slot_stats = []
        for slot in slots:
            slot_records = [r for r in slot_attendance if r.slot_id == slot.id]
            present_count = len([r for r in slot_records if r.status in ['Present', 'Late']])
            absent_count = len([r for r in slot_records if r.status == 'Absent'])
            late_count_slot = len([r for r in slot_records if r.status == 'Late'])
            
            slot_stats.append({
                'slot_id': slot.id,
                'slot_name': slot.class_name,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count_slot,
                'attendance_percent': round((present_count / total_students * 100) if total_students > 0 else 0, 2)
            })
        
        return jsonify({
            'date': date_filter,
            'total_students': total_students,
            'present_today': present_today,
            'attendance_percent': round(attendance_percent, 2),
            'late_count': late_count,
            'avg_duration_minutes': round(avg_duration, 2),
            'currently_inside': currently_inside,
            'slot_statistics': slot_stats,
            'total_slots': len(slots)
        }), 200
    finally:
        session.close()

@app.route('/api/class-time', methods=['GET', 'POST'])
@login_required
def class_time():
    """Get or update class timing settings"""
    session = Session()
    try:
        if request.method == 'GET':
            settings = session.query(ClassSettings).first()
            if settings:
                return jsonify({
                    'class_start_time': settings.class_start_time,
                    'late_threshold_minutes': settings.late_threshold_minutes,
                    'last_updated': settings.last_updated.strftime('%Y-%m-%d %H:%M:%S') if settings.last_updated else None
                }), 200
            else:
                # Return defaults if no settings found
                return jsonify({
                    'class_start_time': '09:00:00',
                    'late_threshold_minutes': 10,
                    'last_updated': None
                }), 200
        else:
            # POST - Update settings
            data = request.get_json()
            class_start_time = data.get('class_start_time')  # Format: "HH:MM:SS" or "HH:MM"
            late_threshold_minutes = data.get('late_threshold_minutes')
            
            # Validate time format
            if class_start_time:
                try:
                    parts = class_start_time.split(':')
                    if len(parts) < 2:
                        return jsonify({'error': 'Invalid time format. Use HH:MM:SS or HH:MM'}), 400
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    
                    if hour < 0 or hour > 23 or minute < 0 or minute > 59 or second < 0 or second > 59:
                        return jsonify({'error': 'Invalid time values'}), 400
                    
                    # Format as HH:MM:SS
                    class_start_time = f"{hour:02d}:{minute:02d}:{second:02d}"
                except ValueError:
                    return jsonify({'error': 'Invalid time format. Use HH:MM:SS or HH:MM'}), 400
            
            # Validate late threshold
            if late_threshold_minutes is not None:
                try:
                    late_threshold_minutes = int(late_threshold_minutes)
                    if late_threshold_minutes < 0:
                        return jsonify({'error': 'Late threshold must be >= 0'}), 400
                except ValueError:
                    return jsonify({'error': 'Late threshold must be a number'}), 400
            
            # Get or create settings
            settings = session.query(ClassSettings).first()
            if not settings:
                settings = ClassSettings(
                    class_start_time=class_start_time or '09:00:00',
                    late_threshold_minutes=late_threshold_minutes or 10
                )
                session.add(settings)
            else:
                if class_start_time:
                    settings.class_start_time = class_start_time
                if late_threshold_minutes is not None:
                    settings.late_threshold_minutes = late_threshold_minutes
                settings.last_updated = datetime.now()
            
            session.commit()
            
            return jsonify({
                'message': 'Class settings updated successfully',
                'class_start_time': settings.class_start_time,
                'late_threshold_minutes': settings.late_threshold_minutes,
                'last_updated': settings.last_updated.strftime('%Y-%m-%d %H:%M:%S')
            }), 200
    except Exception as e:
        session.rollback()
        print(f"Error in class_time endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/class-slots', methods=['GET', 'POST'])
@login_required
def class_slots():
    """Get all class slots or create a new one"""
    session = Session()
    try:
        if request.method == 'GET':
            slots = session.query(ClassSlot).order_by(ClassSlot.start_time).all()
            result = []
            for slot in slots:
                # Calculate duration
                start_parts = slot.start_time.split(':')
                end_parts = slot.end_time.split(':')
                start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
                duration_minutes = end_minutes - start_minutes
                
                result.append({
                    'id': slot.id,
                    'class_name': slot.class_name,
                    'start_time': slot.start_time,
                    'end_time': slot.end_time,
                    'duration_minutes': duration_minutes,
                    'day_of_week': slot.day_of_week,
                    'created_at': slot.created_at.strftime('%Y-%m-%d %H:%M:%S') if slot.created_at else None,
                    'updated_at': slot.updated_at.strftime('%Y-%m-%d %H:%M:%S') if slot.updated_at else None
                })
            return jsonify(result), 200
        else:
            # POST - Create new slot
            data = request.get_json()
            class_name = data.get('class_name') or data.get('subject_name')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            day_of_week = data.get('day_of_week')
            
            if not class_name:
                return jsonify({'error': 'class_name or subject_name is required'}), 400
            if not start_time:
                return jsonify({'error': 'start_time is required (format: HH:MM)'}), 400
            if not end_time:
                return jsonify({'error': 'end_time is required (format: HH:MM)'}), 400
            
            # Validate time format
            try:
                start_parts = start_time.split(':')
                end_parts = end_time.split(':')
                if len(start_parts) < 2 or len(end_parts) < 2:
                    return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
                
                start_hour = int(start_parts[0])
                start_min = int(start_parts[1])
                end_hour = int(end_parts[0])
                end_min = int(end_parts[1])
                
                if start_hour < 0 or start_hour > 23 or start_min < 0 or start_min > 59:
                    return jsonify({'error': 'Invalid start_time values'}), 400
                if end_hour < 0 or end_hour > 23 or end_min < 0 or end_min > 59:
                    return jsonify({'error': 'Invalid end_time values'}), 400
                
                # Format as HH:MM
                start_time = f"{start_hour:02d}:{start_min:02d}"
                end_time = f"{end_hour:02d}:{end_min:02d}"
                
                # Check if end_time is after start_time
                start_total = start_hour * 60 + start_min
                end_total = end_hour * 60 + end_min
                if end_total <= start_total:
                    return jsonify({'error': 'end_time must be after start_time'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
            
            # Create new slot
            slot = ClassSlot(
                class_name=class_name,
                start_time=start_time,
                end_time=end_time,
                day_of_week=day_of_week
            )
            session.add(slot)
            session.commit()
            
            # Calculate duration
            duration_minutes = end_total - start_total
            
            return jsonify({
                'id': slot.id,
                'class_name': slot.class_name,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'duration_minutes': duration_minutes,
                'day_of_week': slot.day_of_week,
                'message': 'Class slot created successfully'
            }), 201
    except Exception as e:
        session.rollback()
        print(f"Error in class_slots endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/class-slots/<int:slot_id>', methods=['PUT', 'DELETE'])
@login_required
def class_slot_detail(slot_id):
    """Update or delete a class slot"""
    session = Session()
    try:
        slot = session.query(ClassSlot).filter(ClassSlot.id == slot_id).first()
        if not slot:
            return jsonify({'error': 'Class slot not found'}), 404
        
        if request.method == 'PUT':
            # Update slot
            data = request.get_json()
            class_name = data.get('class_name') or data.get('subject_name')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            day_of_week = data.get('day_of_week')
            
            if class_name:
                slot.class_name = class_name
            if start_time:
                try:
                    start_parts = start_time.split(':')
                    if len(start_parts) < 2:
                        return jsonify({'error': 'Invalid start_time format. Use HH:MM'}), 400
                    start_hour = int(start_parts[0])
                    start_min = int(start_parts[1])
                    if start_hour < 0 or start_hour > 23 or start_min < 0 or start_min > 59:
                        return jsonify({'error': 'Invalid start_time values'}), 400
                    slot.start_time = f"{start_hour:02d}:{start_min:02d}"
                except ValueError:
                    return jsonify({'error': 'Invalid start_time format. Use HH:MM'}), 400
            if end_time:
                try:
                    end_parts = end_time.split(':')
                    if len(end_parts) < 2:
                        return jsonify({'error': 'Invalid end_time format. Use HH:MM'}), 400
                    end_hour = int(end_parts[0])
                    end_min = int(end_parts[1])
                    if end_hour < 0 or end_hour > 23 or end_min < 0 or end_min > 59:
                        return jsonify({'error': 'Invalid end_time values'}), 400
                    slot.end_time = f"{end_hour:02d}:{end_min:02d}"
                except ValueError:
                    return jsonify({'error': 'Invalid end_time format. Use HH:MM'}), 400
            if day_of_week is not None:
                slot.day_of_week = day_of_week
            
            # Validate end_time is after start_time
            start_parts = slot.start_time.split(':')
            end_parts = slot.end_time.split(':')
            start_total = int(start_parts[0]) * 60 + int(start_parts[1])
            end_total = int(end_parts[0]) * 60 + int(end_parts[1])
            if end_total <= start_total:
                return jsonify({'error': 'end_time must be after start_time'}), 400
            
            slot.updated_at = datetime.now()
            session.commit()
            
            duration_minutes = end_total - start_total
            
            return jsonify({
                'id': slot.id,
                'class_name': slot.class_name,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'duration_minutes': duration_minutes,
                'day_of_week': slot.day_of_week,
                'message': 'Class slot updated successfully'
            }), 200
        else:
            # DELETE
            slot_name = slot.class_name
            session.delete(slot)
            session.commit()
            return jsonify({'message': f'Class slot "{slot_name}" deleted successfully'}), 200
    except Exception as e:
        session.rollback()
        print(f"Error in class_slot_detail endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reports/daily', methods=['GET'])
@login_required
def export_daily_report():
    """Export daily attendance report as Excel or PDF (slot-based)"""
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    format_type = request.args.get('format', 'excel')  # 'excel' or 'pdf'
    
    session = Session()
    try:
        # Get all slots for this date
        slots = get_class_slots_for_date(date_filter)
        
        # Get all students
        all_students = session.query(User).filter(User.status == 'approved').all()
        
        # Get slot attendance records
        slot_attendance_records = session.query(SlotAttendance).filter(
            SlotAttendance.date == date_filter
        ).all()
        
        # Create a map: (user_id, slot_id) -> SlotAttendance
        attendance_map = {}
        for record in slot_attendance_records:
            key = (record.user_id, record.slot_id)
            attendance_map[key] = record
        
        # Build data structure: student -> slots -> status
        data = []
        for student in all_students:
            row = {
                'ID': student.id,
                'Name': student.name,
                'USN': student.usn
            }
            
            # Add status for each slot
            for slot in slots:
                key = (student.id, slot.id)
                if key in attendance_map:
                    record = attendance_map[key]
                    row[f"{slot.class_name} ({slot.start_time}-{slot.end_time})"] = record.status
                    if record.overlap_minutes:
                        row[f"{slot.class_name} Overlap (min)"] = round(record.overlap_minutes, 2)
                else:
                    row[f"{slot.class_name} ({slot.start_time}-{slot.end_time})"] = 'Absent'
            
            data.append(row)
        
        if format_type == 'excel':
            df = pd.DataFrame(data)
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return Response(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attendance_slots_{date_filter}.xlsx'}
            )
        else:  # PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch)
            elements = []
            styles = getSampleStyleSheet()
            
            elements.append(Paragraph(f"Daily Attendance Report (Slot-Based) - {date_filter}", styles['Title']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Build table with slots as columns
            table_data = [['ID', 'Name', 'USN']]
            for slot in slots:
                table_data[0].append(f"{slot.class_name}\n({slot.start_time}-{slot.end_time})")
            
            for row_dict in data:
                row = [str(row_dict['ID']), row_dict['Name'], row_dict['USN']]
                for slot in slots:
                    col_name = f"{slot.class_name} ({slot.start_time}-{slot.end_time})"
                    status = row_dict.get(col_name, 'Absent')
                    row.append(status)
                table_data.append(row)
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            elements.append(table)
            
            doc.build(elements)
            buffer.seek(0)
            return Response(
                buffer,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attendance_slots_{date_filter}.pdf'}
            )
    finally:
        session.close()

@app.route('/api/slot-attendance', methods=['GET'])
@login_required
def get_slot_attendance():
    """Get slot-based attendance for a specific date"""
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    session = Session()
    try:
        # Get all slots for this date
        slots = get_class_slots_for_date(date_filter)
        
        # Get all students
        all_students = session.query(User).filter(User.status == 'approved').all()
        
        # Get slot attendance records
        slot_attendance_records = session.query(SlotAttendance).filter(
            SlotAttendance.date == date_filter
        ).all()
        
        # Create a map: (user_id, slot_id) -> SlotAttendance
        attendance_map = {}
        for record in slot_attendance_records:
            key = (record.user_id, record.slot_id)
            attendance_map[key] = record
        
        # Build response
        result = {
            'date': date_filter,
            'slots': [],
            'students': []
        }
        
        # Add slot information
        for slot in slots:
            result['slots'].append({
                'id': slot.id,
                'class_name': slot.class_name,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'day_of_week': slot.day_of_week
            })
        
        # Add student attendance
        for student in all_students:
            student_data = {
                'user_id': student.id,
                'name': student.name,
                'usn': student.usn,
                'slot_attendance': []
            }
            
            for slot in slots:
                key = (student.id, slot.id)
                if key in attendance_map:
                    record = attendance_map[key]
                    student_data['slot_attendance'].append({
                        'slot_id': slot.id,
                        'slot_name': slot.class_name,
                        'status': record.status,
                        'entry_time': record.entry_time.strftime('%H:%M:%S') if record.entry_time else None,
                        'exit_time': record.exit_time.strftime('%H:%M:%S') if record.exit_time else None,
                        'overlap_minutes': round(record.overlap_minutes, 2) if record.overlap_minutes else 0
                    })
                else:
                    student_data['slot_attendance'].append({
                        'slot_id': slot.id,
                        'slot_name': slot.class_name,
                        'status': 'Absent',
                        'entry_time': None,
                        'exit_time': None,
                        'overlap_minutes': 0
                    })
            
            result['students'].append(student_data)
        
        return jsonify(result), 200
    finally:
        session.close()

@app.route('/api/students/inside', methods=['GET'])
@login_required
def get_students_inside():
    """Get list of students currently inside classroom"""
    with face_recognition_lock:
        inside_list = []
        for user_id, session_data in active_sessions.items():
            inside_list.append({
                'user_id': user_id,
                'name': session_data['user_name'],
                'usn': session_data['user_usn'],
                'entry_time': session_data['entry_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'last_seen': session_data['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify(inside_list), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)


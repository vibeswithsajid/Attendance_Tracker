#!/usr/bin/env python3
"""
Complete Flow Testing Script

This script tests the entire attendance system flow:
1. Check backend status
2. Verify class settings
3. Check student registration
4. Simulate attendance recording
5. Verify data in database

Usage:
    python3 test_complete_flow.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import Session, User, Attendance, ClassSettings, get_class_settings
from datetime import datetime, timedelta, time as dt_time
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_backend():
    """Check if backend components are working"""
    print_section("1. Backend Status Check")
    
    try:
        session = Session()
        
        # Check database connection
        user_count = session.query(User).count()
        attendance_count = session.query(Attendance).count()
        settings = session.query(ClassSettings).first()
        
        print(f"✅ Database connected")
        print(f"   Users: {user_count}")
        print(f"   Attendance records: {attendance_count}")
        
        if settings:
            print(f"   Class Start: {settings.class_start_time}")
            print(f"   Late Threshold: {settings.late_threshold_minutes} min")
        else:
            print(f"   ⚠️  No class settings found (using defaults)")
        
        session.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_students():
    """List all registered students"""
    print_section("2. Registered Students")
    
    try:
        session = Session()
        users = session.query(User).all()
        
        if not users:
            print("   ⚠️  No students registered yet")
            print("   💡 Register a student via Flutter app or admin panel")
            return []
        
        print(f"   Found {len(users)} students:")
        for user in users:
            status_emoji = "✅" if user.status == 'approved' else "⏳" if user.status == 'pending' else "❌"
            print(f"   {status_emoji} {user.name} ({user.usn}) - {user.status}")
        
        session.close()
        return users
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def check_attendance():
    """List recent attendance records"""
    print_section("3. Attendance Records")
    
    try:
        session = Session()
        records = session.query(Attendance).order_by(Attendance.entry_time.desc()).limit(10).all()
        
        if not records:
            print("   ⚠️  No attendance records yet")
            print("   💡 Create attendance records (see simulation methods)")
            return []
        
        print(f"   Found {len(records)} recent records:")
        for r in records:
            status = "⚠️ Late" if r.is_late else "✅ On Time"
            print(f"   {status} {r.user_name} ({r.user_usn}) - {r.entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        session.close()
        return records
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def simulate_attendance(usn, entry_minutes_after_class=5):
    """Simulate attendance entry for a student"""
    print_section(f"4. Simulating Attendance for {usn}")
    
    try:
        session = Session()
        
        # Find user
        user = session.query(User).filter(User.usn == usn.upper()).first()
        if not user:
            print(f"   ❌ Student {usn} not found!")
            print(f"   💡 Register student first via Flutter app or admin panel")
            return False
        
        if user.status != 'approved':
            print(f"   ❌ Student {usn} is not approved (status: {user.status})")
            print(f"   💡 Approve student in admin panel first")
            return False
        
        # Get class settings
        settings = get_class_settings()
        class_start_str = settings['class_start_time']
        late_threshold = settings['late_threshold_minutes']
        
        # Parse class start time
        time_parts = class_start_str.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        # Create entry time
        today = datetime.now().date()
        class_start = datetime.combine(today, dt_time(hour, minute, second))
        entry_time = class_start + timedelta(minutes=entry_minutes_after_class)
        
        # Calculate if late
        late_limit = class_start + timedelta(minutes=late_threshold)
        is_late = 1 if entry_time > late_limit else 0
        
        # Check if record already exists for today
        today_str = today.strftime('%Y-%m-%d')
        existing = session.query(Attendance).filter(
            Attendance.user_id == user.id,
            Attendance.date == today_str
        ).first()
        
        if existing:
            print(f"   ⚠️  Attendance record already exists for today")
            print(f"   💡 Delete existing record or use different date")
            return False
        
        # Create attendance record
        attendance = Attendance(
            user_id=user.id,
            user_name=user.name,
            user_usn=user.usn,
            entry_time=entry_time,
            date=today_str,
            is_late=is_late,
            camera_id='simulated_camera',
            class_start_time=class_start
        )
        session.add(attendance)
        session.commit()
        
        status = "⚠️ Late" if is_late else "✅ On Time"
        print(f"   ✅ Attendance record created:")
        print(f"      Student: {user.name} ({user.usn})")
        print(f"      Entry Time: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      Class Start: {class_start.strftime('%H:%M:%S')}")
        print(f"      Late Limit: {late_limit.strftime('%H:%M:%S')}")
        print(f"      Status: {status}")
        
        session.close()
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("  COMPLETE FLOW SIMULATION TEST")
    print("="*60)
    
    # Step 1: Check backend
    if not check_backend():
        print("\n❌ Backend check failed. Make sure app.py is running!")
        return
    
    # Step 2: Check students
    students = check_students()
    
    # Step 3: Check attendance
    records = check_attendance()
    
    # Step 4: Simulate attendance if student exists
    if students:
        approved_students = [s for s in students if s.status == 'approved']
        if approved_students:
            test_usn = approved_students[0].usn
            print(f"\n💡 Simulating attendance for first approved student: {test_usn}")
            
            # Simulate On Time entry (5 minutes after class start)
            simulate_attendance(test_usn, entry_minutes_after_class=5)
            
            # Simulate Late entry (15 minutes after class start, assuming 10 min threshold)
            print(f"\n💡 Simulating late entry...")
            simulate_attendance(test_usn, entry_minutes_after_class=15)
        else:
            print(f"\n💡 No approved students found. Approve a student first.")
    
    # Final summary
    print_section("5. Test Summary")
    print("✅ Backend: Running")
    print(f"✅ Students: {len(students)} registered")
    print(f"✅ Attendance: {len(records)} records")
    
    if students and any(s.status == 'approved' for s in students):
        print("✅ Ready for full flow testing!")
        print("\n💡 Next steps:")
        print("   1. Open Flutter app and login with student USN")
        print("   2. View attendance in dashboard")
        print("   3. Check admin panel for records")
        print("   4. Verify Late/On Time status")
    else:
        print("⚠️  Complete flow not ready yet")
        print("\n💡 Missing:")
        if not students:
            print("   - Register at least one student")
        elif not any(s.status == 'approved' for s in students):
            print("   - Approve at least one student")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


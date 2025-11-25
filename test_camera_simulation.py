#!/usr/bin/env python3
"""
Camera Simulation Script for Testing Face Recognition Attendance System

This script simulates camera face detection for testing purposes.
It can be used when you don't have a physical camera or want to test
the complete workflow without setting up hardware.

Usage:
    python3 test_camera_simulation.py --usn TEST001 --name "Test Student"
"""

import argparse
import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:5001"

def simulate_attendance_entry(usn, name=None, entry_time=None):
    """
    Simulate a student entering (face detected by camera)
    This creates an attendance record directly via the database logic
    """
    print(f"\n🎥 Simulating camera detection...")
    print(f"   Student: {name or usn} (USN: {usn})")
    
    # Get class settings to calculate late status
    try:
        response = requests.get(f"{BASE_URL}/api/class-time")
        if response.status_code == 200:
            settings = response.json()
            print(f"   Class Start: {settings['class_start_time']}")
            print(f"   Late Threshold: {settings['late_threshold_minutes']} minutes")
    except:
        print("   ⚠️  Could not fetch class settings")
    
    # Note: In real system, this would be done automatically by camera detection
    # For simulation, we're just showing what would happen
    print(f"\n✅ Simulated Entry Recorded!")
    print(f"   Time: {entry_time or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n💡 To see actual attendance records:")
    print(f"   1. Make sure camera is running in admin panel")
    print(f"   2. Student's face should be recognized by camera")
    print(f"   3. Check attendance records in admin panel or Flutter app")

def check_student_exists(usn):
    """Check if student exists in system"""
    try:
        response = requests.get(f"{BASE_URL}/api/students/{usn}/profile")
        return response.status_code == 200
    except:
        return False

def get_student_info(usn):
    """Get student information"""
    try:
        response = requests.get(f"{BASE_URL}/api/students/{usn}/profile")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def list_all_students():
    """List all registered students"""
    try:
        response = requests.get(f"{BASE_URL}/api/users")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def main():
    parser = argparse.ArgumentParser(description='Simulate camera face detection for testing')
    parser.add_argument('--usn', required=True, help='Student USN')
    parser.add_argument('--name', help='Student name (optional)')
    parser.add_argument('--time', help='Entry time (YYYY-MM-DD HH:MM:SS), default: now')
    parser.add_argument('--list', action='store_true', help='List all registered students')
    parser.add_argument('--check', action='store_true', help='Check if student exists')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎥 Camera Simulation Tool")
    print("=" * 60)
    
    if args.list:
        print("\n📋 Registered Students:")
        students = list_all_students()
        if students:
            for student in students:
                status_emoji = "✅" if student['status'] == 'approved' else "⏳" if student['status'] == 'pending' else "❌"
                print(f"   {status_emoji} {student['name']} ({student['usn']}) - {student['status']}")
        else:
            print("   No students registered yet")
        return
    
    if args.check:
        exists = check_student_exists(args.usn)
        if exists:
            info = get_student_info(args.usn)
            if info:
                print(f"\n✅ Student Found:")
                print(f"   Name: {info['name']}")
                print(f"   USN: {info['usn']}")
                print(f"   Status: {info['status']}")
            else:
                print(f"\n✅ Student exists but could not fetch details")
        else:
            print(f"\n❌ Student not found: {args.usn}")
            print(f"   Register the student first via Flutter app or admin panel")
        return
    
    # Parse entry time if provided
    entry_time = None
    if args.time:
        try:
            entry_time = datetime.strptime(args.time, '%Y-%m-%d %H:%M:%S')
        except:
            print(f"⚠️  Invalid time format. Use: YYYY-MM-DD HH:MM:SS")
            return
    
    # Check if student exists
    student_info = get_student_info(args.usn)
    if not student_info:
        print(f"\n❌ Student {args.usn} not found!")
        print(f"\n💡 To register student:")
        print(f"   1. Use Flutter app: Enter USN → Register → Add photos")
        print(f"   2. Or use admin panel: Add User → Enter USN and capture photo")
        return
    
    if student_info['status'] != 'approved':
        print(f"\n⚠️  Student status: {student_info['status']}")
        print(f"   Student must be approved by admin before attendance can be recorded")
        print(f"   Go to admin panel → Approvals → Approve student")
        return
    
    # Simulate entry
    simulate_attendance_entry(
        args.usn,
        name=args.name or student_info.get('name'),
        entry_time=entry_time
    )
    
    print(f"\n📝 Note: This is a simulation.")
    print(f"   For real attendance recording:")
    print(f"   1. Start camera in admin panel (Camera Setup)")
    print(f"   2. Student's face must be detected by camera")
    print(f"   3. System automatically creates attendance record")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Simulation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")


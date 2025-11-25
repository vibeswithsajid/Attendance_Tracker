# Camera Setup & Simulation Guide

## 🎥 Camera Options

### Option 1: Use Webcam (Easiest for Testing)

**For macOS/Linux:**
```bash
# Check available cameras
ls /dev/video*

# Usually camera index is 0 for built-in webcam
```

**For Windows:**
- Built-in webcam is usually index `0`
- External USB cameras start from `1`, `2`, etc.

### Option 2: Use IP Camera / RTSP Stream

**Format:**
```
rtsp://username:password@ip_address:port/stream_path
```

**Example:**
```
rtsp://admin:password123@192.168.1.100:554/stream1
```

### Option 3: Use Video File (For Testing/Simulation)

You can modify the code to use a video file instead of live camera for testing.

## 🚀 Quick Start - Camera Setup

### Step 1: Start Backend
```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py
```

### Step 2: Open Admin Panel
1. Go to `http://localhost:5001`
2. Login: `admin@gmail.com` / `admin`

### Step 3: Setup Camera
1. Click **"📷 Camera Setup"** button
2. Enter Camera ID: `door_camera` (or any name)
3. Enter Camera URL/Index:
   - For webcam: `0` (or `1` if `0` doesn't work)
   - For IP camera: `rtsp://username:password@ip:port/stream`
4. Click **"Start Camera"**

### Step 4: Verify Camera is Working
- You should see live video feed in the main dashboard
- Camera status should show "Camera ready - Face recognition active"
- If camera fails, try different index (1, 2, etc.)

## 🧪 Testing Without Real Camera (Simulation)

### Method 1: Use Test Images

Create a test script to simulate face detection:

```python
# test_camera_simulation.py
import cv2
import face_recognition
import numpy as np
from datetime import datetime
import requests
import json

# Load a test image with known face
test_image_path = "test_face.jpg"  # Put a test image here
image = face_recognition.load_image_file(test_image_path)
face_encoding = face_recognition.face_encodings(image)[0]

# Simulate attendance entry
def simulate_entry(user_id, user_name, user_usn):
    current_time = datetime.now()
    
    # Make API call to simulate entry
    # This would normally come from camera detection
    print(f"Simulated Entry: {user_name} ({user_usn}) at {current_time}")
    
    # You can manually create attendance records via API
    # Or use the admin panel to add test attendance
```

### Method 2: Use Video File

Modify `process_camera_feed` function temporarily:

```python
# In app.py, modify process_camera_feed function
def process_camera_feed(camera_id, camera_url):
    # If camera_url is a file path (ends with .mp4, .avi, etc.)
    if isinstance(camera_url, str) and camera_url.endswith(('.mp4', '.avi', '.mov')):
        cap = cv2.VideoCapture(camera_url)  # Use video file
    else:
        cap = cv2.VideoCapture(camera_url)  # Use camera
    
    # Rest of the code...
```

Then in Camera Setup, enter video file path instead of camera index.

### Method 3: Manual Attendance Entry (For Testing)

Use the admin panel or API to manually create attendance records:

```bash
# Using curl (after starting backend)
curl -X POST http://localhost:5001/api/attendance/manual \
  -H "Content-Type: application/json" \
  -d '{
    "user_usn": "1ABC20CS001",
    "entry_time": "2024-11-25 09:05:00",
    "is_late": false
  }'
```

## 📋 Complete Testing Workflow

### 1. Setup Test Student
```bash
# Via Admin Panel:
1. Login to admin panel
2. Click "➕ Add User"
3. Enter Name: "Test Student"
4. Enter USN: "TEST001"
5. Capture face photo
6. Click "Add User"
```

### 2. Setup Camera
```bash
# Via Admin Panel:
1. Click "📷 Camera Setup"
2. Camera ID: "test_camera"
3. Camera URL: "0" (for webcam)
4. Click "Start Camera"
```

### 3. Test Face Recognition
- Stand in front of camera (or show test student's photo)
- System should detect face and create attendance record
- Check "Real-Time Alerts" panel for entry notification
- Check "Attendance Records" table for new entry

### 4. Verify in Flutter App
- Student logs in with USN: "TEST001"
- Should see attendance record in dashboard
- Should show Late/On Time status

## 🔧 Camera Troubleshooting

### Camera Not Opening
**Problem:** Camera index 0 doesn't work

**Solutions:**
1. Try different indices: 1, 2, 3, etc.
2. Check if camera is being used by another app
3. On macOS, grant camera permissions to Terminal/Python
4. Check camera in system settings

### No Face Detection
**Problem:** Camera works but no faces detected

**Solutions:**
1. Ensure good lighting
2. Face should be clearly visible
3. Check if student is registered and approved
4. Verify face encodings are loaded (check console logs)

### Camera Feed Not Showing
**Problem:** Camera starts but no video feed

**Solutions:**
1. Check browser console for errors
2. Verify camera is actually running (check backend logs)
3. Try refreshing the page
4. Check if camera supports the requested resolution

## 📝 Camera Configuration Options

### Resolution Settings
In `app.py`, you can modify camera resolution:

```python
# In process_camera_feed function
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Increase for better quality
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

### Frame Processing Rate
```python
# Process every Nth frame (reduce CPU usage)
process_this_frame = frame_count % 3 == 0  # Process every 3rd frame
```

### Face Recognition Tolerance
```python
# In process_camera_feed function
matches = face_recognition.compare_faces(
    known_face_encodings, 
    face_encoding, 
    tolerance=0.5  # Lower = stricter matching
)
```

## 🎯 Production Camera Setup

### For Real Deployment:

1. **Use IP Cameras:**
   - More reliable than USB webcams
   - Can be placed at entrance
   - Use RTSP streams

2. **Multiple Cameras:**
   - Each camera needs unique Camera ID
   - Can run multiple cameras simultaneously
   - Each processes independently

3. **Camera Placement:**
   - Mount at eye level
   - Good lighting
   - Clear view of entrance
   - Avoid backlighting

4. **Network Setup:**
   - Ensure cameras are on same network
   - Use static IP addresses
   - Configure firewall rules if needed

## 📱 Testing Checklist

- [ ] Backend running on port 5001
- [ ] At least one student registered and approved
- [ ] Camera started in admin panel
- [ ] Live video feed visible
- [ ] Face detection working (check alerts)
- [ ] Attendance records created
- [ ] Flutter app shows attendance history
- [ ] Late/On Time status correct
- [ ] Class timings displayed correctly

## 🐛 Common Issues

**Issue:** "No users registered" error when starting camera
- **Fix:** Register at least one student first

**Issue:** Camera starts but immediately stops
- **Fix:** Check camera permissions, try different index

**Issue:** Faces detected but not recognized
- **Fix:** Ensure student is approved, check face encodings loaded

**Issue:** Attendance not showing in Flutter app
- **Fix:** Check student USN matches, refresh app, verify API connection


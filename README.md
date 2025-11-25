# Face Recognition Attendance System

A complete face recognition-based attendance tracking system with web admin panel and Flutter mobile app.

## 🚀 Quick Start

### 1. Start Backend
```bash
python3 app.py
```
Backend runs on `http://localhost:5001`

### 2. Access Admin Panel
- URL: `http://localhost:5001`
- Login: `admin@gmail.com` / `admin`
- Click **"⚙️ Settings"** → Set class timings
- Click **"📷 Camera Setup"** → Start camera (use `0` for webcam)

### 3. Run Flutter App
```bash
cd flutter_app
flutter pub get
flutter run
```

## 📁 Project Structure

```
Project/
├── app.py                    # Main Flask backend
├── requirements.txt          # Python dependencies
├── templates/                # HTML templates (admin panel)
├── static/                   # CSS, JS for web panel
├── uploads/                  # Student uploaded photos
├── flutter_app/              # Flutter mobile application
│   ├── lib/
│   │   ├── models/           # Data models
│   │   ├── screens/          # UI screens
│   │   └── services/         # API services
│   └── pubspec.yaml
├── archive/                  # Old/unused code (for reference)
└── Documentation/
    ├── COMPLETE_WORKFLOW.md  # Detailed workflow guide
    ├── CAMERA_SETUP_GUIDE.md # Camera setup & troubleshooting
    └── SYSTEM_OVERVIEW.md    # Complete API documentation
```

## ✨ Features

### Backend (Flask)
- ✅ Student registration with multiple photos
- ✅ Admin approval/rejection system
- ✅ Class timing settings (database)
- ✅ Late detection logic
- ✅ Camera face recognition
- ✅ Real-time attendance recording
- ✅ Analytics and reports (Excel/PDF)

### Admin Web Panel
- ✅ Live camera feed
- ✅ Real-time alerts
- ✅ Settings management
- ✅ Student management
- ✅ Approval system
- ✅ Analytics dashboard
- ✅ Report export

### Flutter Mobile App
- ✅ Smart login/registration flow
- ✅ Photo capture (2-5 photos)
- ✅ Class timing display
- ✅ Attendance history
- ✅ Late/On Time status

## 🔄 Complete Workflow

```
1. Student Registration
   Flutter App → Register with USN + Photos → Database (pending)

2. Admin Approval
   Admin Panel → Review → Approve/Reject → Database (approved)

3. Face Detection
   Camera → Detect Face → Recognize → Create Attendance Record

4. View Attendance
   Flutter App / Admin Panel → View History → See Late/On Time Status
```

## 📚 Documentation

### Main Guides
- **`COMPLETE_WORKFLOW.md`** - End-to-end workflow and testing scenarios
- **`CAMERA_SETUP_GUIDE.md`** - Camera setup, simulation, troubleshooting
- **`SYSTEM_OVERVIEW.md`** - Complete API documentation and system architecture

### Flutter App
- **`flutter_app/README.md`** - Flutter app setup, integration, and API usage

### Quick Navigation
- **Getting Started?** → Read this `README.md`
- **Setting up camera?** → Read `CAMERA_SETUP_GUIDE.md`
- **Understanding workflow?** → Read `COMPLETE_WORKFLOW.md`
- **API integration?** → Read `SYSTEM_OVERVIEW.md`
- **Flutter development?** → Read `flutter_app/README.md`

## 📋 Requirements

- Python 3.8+
- Flask, face_recognition, OpenCV
- SQLite database
- Flutter SDK 3.0+ (for mobile app)
- Camera (webcam or IP camera)

## 🔧 Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# For Flutter app
cd flutter_app
flutter pub get
```

## 🧪 Testing Without Camera

Use the simulation script:
```bash
python3 test_camera_simulation.py --list          # List all students
python3 test_camera_simulation.py --check --usn TEST001  # Check student
```

## 🐛 Troubleshooting

**Backend won't start:**
- Check port 5001 is available
- Install dependencies: `pip install -r requirements.txt`

**Camera not working:**
- Try different camera index (0, 1, 2...)
- Check camera permissions
- See `CAMERA_SETUP_GUIDE.md`

**Flutter app can't connect:**
- Check backend URL in `api_service.dart`
- For emulator: use `10.0.2.2:5001` (Android) or `localhost:5001` (iOS)
- For physical device: use your computer's IP address

**Student can't login:**
- Check student is approved in admin panel
- Verify USN is correct
- Check backend is running

## 📝 License

This project is open source and available for modification and distribution.

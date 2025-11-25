# Flutter Attendance App

Student mobile application for the Face Recognition Attendance System.

## 🚀 Quick Start

### 1. Install Flutter
```bash
flutter --version
```
If not installed: https://flutter.dev/docs/get-started/install

### 2. Install Dependencies
```bash
cd flutter_app
flutter pub get
```

### 3. Configure Backend URL
Edit `lib/services/api_service.dart`:

**Android Emulator:**
```dart
static const String baseUrl = 'http://10.0.2.2:5001';
```

**iOS Simulator:**
```dart
static const String baseUrl = 'http://localhost:5001';
```

**Physical Device:**
```dart
static const String baseUrl = 'http://YOUR_IP_ADDRESS:5001';
// Find IP: ifconfig (macOS/Linux) or ipconfig (Windows)
```

### 4. Start Backend
```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py
```

### 5. Run Flutter App
```bash
flutter run
```

## 📱 Features

- ✅ Smart login/registration flow
- ✅ Photo capture (2-5 photos for better recognition)
- ✅ Class timing display
- ✅ Attendance history with Late/On Time status
- ✅ Real-time updates
- ✅ Auto-login persistence

## 🔄 Student Registration & Login Flow

### Step 1: Enter USN
- Student enters USN (e.g., "1ABC20CS001")
- Clicks "Login"

### Step 2A: USN Doesn't Exist → Registration
- App automatically shows Registration screen
- Student enters:
  - Full Name
  - Password (optional)
  - Takes/selects 2-5 face photos
- Clicks "Register"
- Status: **Pending** (waiting for admin approval)

### Step 2B: USN Exists → Login
- App checks USN in database
- If approved → Shows Dashboard
- If pending → Shows "Waiting for approval" message

### Step 3: View Attendance
- Dashboard shows:
  - Welcome card with name and USN
  - Class timing information
  - Late threshold warning
  - Attendance history with Late/On Time status

## 📁 Project Structure

```
flutter_app/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── models/                   # Data models
│   │   ├── class_timings.dart
│   │   ├── attendance_record.dart
│   │   └── user.dart
│   ├── services/                 # API and storage services
│   │   ├── api_service.dart
│   │   └── storage_service.dart
│   └── screens/                  # UI screens
│       ├── login_screen.dart
│       ├── registration_screen.dart
│       └── dashboard_screen.dart
├── pubspec.yaml                  # Dependencies
└── README.md                     # This file
```

## 🔌 API Integration

### Class Timings
```dart
// Get class timings
final timings = await ApiService.getClassTimings();
// Returns: classStartTime, lateThresholdMinutes, lastUpdated
```

### Student Login
```dart
// Login with USN
final user = await ApiService.studentLogin(usn, password: password);
// Returns: User object with id, name, usn, status
```

### Student Registration
```dart
// Register with photos
final user = await ApiService.registerStudent(
  name: name,
  usn: usn,
  password: password,
  images: selectedImages, // List<File>
);
```

### Attendance History
```dart
// Get attendance records
final records = await ApiService.getAttendance(usn, date: date);
// Returns: List<AttendanceRecord> with entry/exit times, isLate status
```

## 🧪 Testing

### 1. Create Test Student
1. Open Flutter app
2. Enter new USN: "TEST001"
3. Register with name and photos
4. Go to admin panel → Approvals → Approve student
5. Login with same USN in Flutter app

### 2. Test Attendance
1. Ensure camera is running in admin panel
2. Student's face is recognized by camera
3. Refresh attendance history in app
4. New record appears with Late/On Time status

## 🐛 Troubleshooting

**Connection Issues:**
- Ensure backend is running: `python3 app.py`
- Check backend URL in `api_service.dart`
- For physical device, ensure same network
- Check firewall settings

**Login Issues:**
- Verify student is registered and approved
- Check USN is correct (case-insensitive)
- Ensure backend is running

**No Attendance Records:**
- Ensure camera is running in admin panel
- Student's face must be recognized
- Check if attendance was recorded in admin panel

## 📝 Notes

- App stores login state locally using SharedPreferences
- Class timings fetched on login and can be refreshed
- Attendance records show late/on-time status based on server calculation
- All API calls made to local backend server

## 📚 Related Documentation

- `../COMPLETE_WORKFLOW.md` - Complete system workflow
- `../CAMERA_SETUP_GUIDE.md` - Camera setup guide
- `../SYSTEM_OVERVIEW.md` - API documentation

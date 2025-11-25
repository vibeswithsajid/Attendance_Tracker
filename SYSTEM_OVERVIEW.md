# Complete Face Recognition Attendance System - Overview

## 🎯 System Features

### 1. Single Door Entry/Exit Detection
- Camera placed at classroom door
- Automatic entry detection when face is recognized
- Exit detection when face disappears (30-second timeout)
- Tracks direction and timestamps correctly
- Prevents duplicate logs

### 2. Student Registration with Approval Workflow
- Students register via Flutter app with:
  - Name
  - USN (University Serial Number)
  - 3-5 face photos
- Admin approval/rejection system
- Status tracking: `pending`, `approved`, `rejected`
- Only approved students are recognized

### 3. Real-Time Alerts
- Entry alerts: "Student X entered at 9:05 AM"
- Exit alerts: "Student Y exited at 10:20 AM"
- Late alerts: "Student Z entered LATE at 9:15 AM"
- Auto-refreshes every 3 seconds
- Alert panel in admin dashboard

### 4. Late Detection
- Configurable class start time (stored in SQLite database)
- Configurable late threshold (default: 10 minutes)
- Late calculation: `late_limit = class_start_time + late_threshold_minutes`
- If student enters after `late_limit` → marked as **Late**
- If student enters before or within grace period → marked as **On Time**
- Automatically marks attendance records
- Shows in analytics, reports, and attendance history

### 5. Admin Web Application Features

#### Dashboard
- Live camera feed
- Real-time alerts panel
- Current time display
- Attendance records with late/on-time status

#### Settings Page
- Configure class start time (HH:MM:SS format)
- Configure late threshold (minutes)
- View last updated timestamp
- Save settings with confirmation

#### Attendance Management
- View today's attendance records
- Entry/Exit timestamps
- Duration calculation
- In-progress sessions highlighted

#### Student Management
- Add users (auto-approved)
- View all registered students
- Delete students
- View student status

#### Approval System
- View pending registrations
- Approve/Reject students
- View registration photos
- Track approval history

#### Analytics Dashboard
- Total students count
- Present today count
- Attendance percentage
- Late students count
- Average duration
- Currently inside count
- Date-filtered analytics

#### Report Export
- Daily attendance reports
- Excel (.xlsx) format
- PDF format
- Includes: ID, Name, USN, Entry, Exit, Duration, Status (Late/On Time), Class Start Time, Late Threshold

### 6. Flutter Mobile App APIs

#### Student Endpoints
- `POST /api/students/register` - Register with multiple photos
- `POST /api/students/login` - Login with USN
- `GET /api/students/<usn>/attendance` - Get attendance history
- `GET /api/students/<usn>/profile` - Get profile
- `PUT /api/students/<usn>/profile` - Update profile photos

#### Admin Endpoints
- `GET /api/admin/approvals` - Get pending approvals
- `POST /api/admin/approve/<id>` - Approve student
- `POST /api/admin/reject/<id>` - Reject student

### 7. Database Schema

#### User Table
- `id` - Primary key
- `name` - Student name
- `usn` - University Serial Number (unique)
- `password` - Optional password
- `face_encodings` - JSON array of face encodings (3-5 per user)
- `image_paths` - JSON array of image paths
- `status` - pending/approved/rejected
- `created_at` - Registration timestamp
- `approved_at` - Approval timestamp
- `approved_by` - Admin who approved

#### Attendance Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `user_name` - Student name (denormalized)
- `user_usn` - USN (denormalized)
- `entry_time` - Entry timestamp
- `exit_time` - Exit timestamp
- `duration_minutes` - Calculated duration
- `camera_id` - Camera identifier
- `is_late` - Late flag (0 = On Time, 1 = Late)
- `class_start_time` - Class start time (datetime) for this record
- `date` - Date string (YYYY-MM-DD) for easy querying

#### Class Settings Table
- `id` - Primary key
- `class_start_time` - Class start time (TEXT, format: "HH:MM:SS", default: "09:00:00")
- `late_threshold_minutes` - Minutes after class start to mark as late (INTEGER, default: 10)
- `last_updated` - Timestamp of last update

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Run the Application
```bash
python3 app.py
```

### 3. Access the System
- Admin Web App: http://localhost:5001
- Login: admin@gmail.com / admin

### 4. Setup Camera
1. Click "Camera Setup" button
2. Enter Camera ID (e.g., "door_camera")
3. Enter camera URL/index (0 for webcam)
4. Click "Start Camera"

### 5. Configure Class Settings
1. Click "⚙️ Settings" button in the header
2. Set Class Start Time (e.g., 09:00:00)
3. Set Late Threshold in minutes (e.g., 10)
4. Click "Save Settings"
5. System will mark students as late if they enter after (Class Start Time + Threshold)

## 📱 Flutter App Integration

### Student Registration
```dart
// POST /api/students/register
FormData formData = FormData.fromMap({
  'name': 'John Doe',
  'usn': '1ABC20CS001',
  'password': 'optional_password',
  'images': [
    MultipartFile.fromFile(photo1),
    MultipartFile.fromFile(photo2),
    MultipartFile.fromFile(photo3),
  ],
});
```

### Student Login
```dart
// POST /api/students/login
{
  "usn": "1ABC20CS001",
  "password": "optional_password"
}
```

### Get Attendance
```dart
// GET /api/students/1ABC20CS001/attendance?date=2024-11-25
// Returns attendance records with is_late flag
```

### Get Class Timings
```dart
// GET /api/class-time
// Returns: {
//   "class_start_time": "09:00:00",
//   "late_threshold_minutes": 10,
//   "last_updated": "2024-11-25 10:30:00"
// }
```

## 🔧 API Endpoints Summary

### Admin Endpoints
- `GET /api/users` - Get all users
- `POST /api/users` - Add user (admin, auto-approved)
- `DELETE /api/users/<id>` - Delete user
- `GET /api/attendance` - Get attendance records (includes is_late status)
- `GET /api/active-sessions` - Get currently inside students
- `GET /api/alerts` - Get real-time alerts
- `POST /api/alerts/clear` - Clear alerts
- `GET /api/analytics` - Get analytics (includes late_count)
- `GET /api/reports/daily?date=YYYY-MM-DD&format=excel|pdf` - Export daily report
- `GET /api/class-time` - Get class timing settings
- `POST /api/class-time` - Update class timing settings (requires JSON body with class_start_time and/or late_threshold_minutes)

### Student Endpoints
- `POST /api/students/register` - Register new student
- `POST /api/students/login` - Student login
- `GET /api/students/<usn>/attendance` - Get attendance history
- `GET /api/students/<usn>/profile` - Get profile
- `PUT /api/students/<usn>/profile` - Update profile

## 📊 Features Summary

✅ Single door entry/exit detection  
✅ Multi-face recognition  
✅ Student registration with approval  
✅ Real-time alerts  
✅ Late detection  
✅ Analytics dashboard  
✅ PDF/Excel export  
✅ Flutter app APIs  
✅ Attendance history  
✅ Profile management  

## 🔐 Security Notes

- Admin login required for web interface
- Student login optional (can use USN only)
- All endpoints require authentication (except student registration)
- Change `app.secret_key` in production
- Use environment variables for credentials

## 📝 Notes

- Database auto-migrates on startup
- Face recognition uses multiple encodings per user for better accuracy
- Exit detection uses 30-second timeout
- Reports can be exported in Excel or PDF format
- Class settings are stored in SQLite database (class_settings table)
- Default class start time: 09:00:00
- Default late threshold: 10 minutes
- Late detection: Entry time > (Class Start Time + Late Threshold) = Late
- System works completely locally
- Can be migrated to cloud/server later

## 🔧 API Documentation Details

### GET /api/class-time
**Description:** Get current class timing settings  
**Authentication:** Required (Admin)  
**Response:**
```json
{
  "class_start_time": "09:00:00",
  "late_threshold_minutes": 10,
  "last_updated": "2024-11-25 10:30:00"
}
```

### POST /api/class-time
**Description:** Update class timing settings  
**Authentication:** Required (Admin)  
**Request Body:**
```json
{
  "class_start_time": "09:00:00",  // Optional, format: "HH:MM:SS" or "HH:MM"
  "late_threshold_minutes": 10      // Optional, integer >= 0
}
```
**Response:**
```json
{
  "message": "Class settings updated successfully",
  "class_start_time": "09:00:00",
  "late_threshold_minutes": 10,
  "last_updated": "2024-11-25 10:30:00"
}
```

### How Late Detection Works

1. **Class Start Time:** Set by admin (e.g., 09:00:00)
2. **Late Threshold:** Set by admin (e.g., 10 minutes)
3. **Late Limit Calculation:** `late_limit = class_start_time + late_threshold_minutes`
   - Example: 09:00:00 + 10 minutes = 09:10:00
4. **Entry Evaluation:**
   - If `entry_time <= late_limit` → **On Time**
   - If `entry_time > late_limit` → **Late**
5. **Storage:** Each attendance record stores:
   - `is_late` flag (0 = On Time, 1 = Late)
   - `class_start_time` (datetime) for reference

### Example Scenarios

**Scenario 1: On Time Entry**
- Class Start: 09:00:00
- Late Threshold: 10 minutes
- Late Limit: 09:10:00
- Student Entry: 09:08:00
- Result: **On Time** (09:08:00 <= 09:10:00)

**Scenario 2: Late Entry**
- Class Start: 09:00:00
- Late Threshold: 10 minutes
- Late Limit: 09:10:00
- Student Entry: 09:15:00
- Result: **Late** (09:15:00 > 09:10:00)

**Scenario 3: Exactly at Late Limit**
- Class Start: 09:00:00
- Late Threshold: 10 minutes
- Late Limit: 09:10:00
- Student Entry: 09:10:00
- Result: **On Time** (09:10:00 <= 09:10:00)


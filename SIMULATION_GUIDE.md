# Complete Flow Simulation Guide

This guide helps you test the entire attendance system without needing a physical camera or real face detection.

## 🎯 Complete Flow Overview

```
1. Backend Setup → 2. Student Registration → 3. Admin Approval → 
4. Simulate Attendance → 5. View Results
```

---

## Step 1: Start Backend Server

```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5001
 * Running on http://0.0.0.0:5001
```

✅ Backend is running if you see this.

**Verify Backend:**
```bash
curl http://localhost:5001/api/status
```

Should return JSON with system status.

---

## Step 2: Configure Class Settings (Admin Panel)

1. Open browser: `http://localhost:5001`
2. Login: `admin@gmail.com` / `admin`
3. Click **"⚙️ Settings"**
4. Set:
   - Class Start Time: `09:00:00`
   - Late Threshold: `10` minutes
5. Click **"💾 Save Settings"**

✅ Class settings saved to database.

---

## Step 3: Student Registration (Flutter App)

### Option A: Using Flutter App (Recommended)

1. **Start Flutter App:**
   ```bash
   cd flutter_app
   flutter run
   ```

2. **Register New Student:**
   - Enter USN: `TEST001`
   - Click "Login"
   - App shows Registration screen (since USN doesn't exist)
   - Enter Name: `Test Student`
   - Take/Select 2-5 photos
   - Click "Register"
   - See success message

3. **Check Registration:**
   - Go to admin panel → **"✅ Approvals"**
   - You should see "Test Student" with status "pending"

### Option B: Using Admin Panel (Quick Test)

1. Open admin panel: `http://localhost:5001`
2. Click **"➕ Add User"**
3. Enter:
   - Name: `Test Student`
   - USN: `TEST001`
4. Capture face photo
5. Click **"Add User"**

✅ Student registered (auto-approved if via admin panel).

---

## Step 4: Admin Approval (If Registered via Flutter)

1. Open admin panel: `http://localhost:5001`
2. Click **"✅ Approvals"**
3. See pending student: "Test Student (TEST001)"
4. Review photos
5. Click **"✅ Approve"**

✅ Student status changed to "approved".

**Verify:**
```bash
curl http://localhost:5001/api/users
```

Should show student with `"status": "approved"`.

---

## Step 5: Simulate Attendance Recording

### Method 1: Using Simulation Script

```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 test_camera_simulation.py --usn TEST001 --name "Test Student"
```

This simulates what would happen when camera detects the student.

### Method 2: Manual API Call (Create Attendance Record)

Since we can't use real camera, we'll create attendance records manually:

```bash
# Create a test attendance record via Python
python3 << 'EOF'
import requests
from datetime import datetime

# Create attendance record manually
response = requests.post('http://localhost:5001/api/attendance/manual', json={
    'user_usn': 'TEST001',
    'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'is_late': False
})
print(response.json())
EOF
```

**Note:** You'll need to add a manual endpoint or use the database directly.

### Method 3: Direct Database Insert (For Testing)

```bash
python3 << 'EOF'
from app import Session, Attendance, User
from datetime import datetime

session = Session()
try:
    user = session.query(User).filter(User.usn == 'TEST001').first()
    if user:
        # Create attendance record
        attendance = Attendance(
            user_id=user.id,
            user_name=user.name,
            user_usn=user.usn,
            entry_time=datetime.now(),
            date=datetime.now().strftime('%Y-%m-%d'),
            is_late=0,
            camera_id='simulated_camera'
        )
        session.add(attendance)
        session.commit()
        print(f"✅ Attendance record created for {user.name}")
    else:
        print("❌ User not found")
finally:
    session.close()
EOF
```

---

## Step 6: View Attendance (Flutter App)

1. **Open Flutter App**
2. **Login with USN:** `TEST001`
3. **Dashboard Shows:**
   - Welcome card with student name
   - Class timing information
   - Attendance history with the record you created

✅ Attendance visible in app.

---

## Step 7: View Attendance (Admin Panel)

1. Open admin panel: `http://localhost:5001`
2. Scroll to **"Attendance Records"** table
3. See the attendance record with:
   - Student name
   - Entry time
   - Status (Late/On Time)

✅ Attendance visible in admin panel.

---

## 🧪 Complete Test Scenario

### Full End-to-End Test

```bash
# Terminal 1: Start Backend
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py

# Terminal 2: Create Test Data
python3 << 'EOF'
import requests
from datetime import datetime
import time

BASE_URL = "http://localhost:5001"

print("🧪 Starting Complete Flow Simulation...\n")

# Step 1: Check backend
print("1. Checking backend...")
try:
    r = requests.get(f"{BASE_URL}/api/status")
    print(f"   ✅ Backend running: {r.status_code == 200}")
except:
    print("   ❌ Backend not running! Start it first.")
    exit(1)

# Step 2: Check class settings
print("\n2. Checking class settings...")
r = requests.get(f"{BASE_URL}/api/class-time")
if r.status_code == 200:
    settings = r.json()
    print(f"   ✅ Class Start: {settings['class_start_time']}")
    print(f"   ✅ Late Threshold: {settings['late_threshold_minutes']} min")
else:
    print("   ⚠️  Could not fetch settings (login required)")

# Step 3: List students
print("\n3. Checking registered students...")
r = requests.get(f"{BASE_URL}/api/users")
if r.status_code == 200:
    users = r.json()
    print(f"   ✅ Found {len(users)} registered students")
    for u in users[:3]:  # Show first 3
        print(f"      - {u['name']} ({u['usn']}) - {u['status']}")
else:
    print("   ⚠️  Could not fetch users (login required)")

# Step 4: Check attendance
print("\n4. Checking attendance records...")
r = requests.get(f"{BASE_URL}/api/attendance")
if r.status_code == 200:
    records = r.json()
    print(f"   ✅ Found {len(records)} attendance records")
    if records:
        latest = records[0]
        print(f"      Latest: {latest['name']} at {latest['entry']} - {'Late' if latest['is_late'] else 'On Time'}")
else:
    print("   ⚠️  Could not fetch attendance (login required)")

print("\n✅ Simulation check complete!")
print("\n💡 Next steps:")
print("   1. Register student via Flutter app")
print("   2. Approve in admin panel")
print("   3. Create attendance record (see methods above)")
print("   4. View in Flutter app and admin panel")
EOF
```

---

## 🎬 Step-by-Step Simulation

### Scenario: New Student Registration & Attendance

**Step 1: Register Student**
```bash
# Via Flutter app or admin panel
# USN: TEST001
# Name: Test Student
# Photos: 3 face photos
```

**Step 2: Approve Student**
```bash
# Admin panel → Approvals → Approve TEST001
```

**Step 3: Create Attendance Record**
```bash
python3 << 'EOF'
from app import Session, Attendance, User, get_class_settings
from datetime import datetime, timedelta, time as dt_time

session = Session()
try:
    user = session.query(User).filter(User.usn == 'TEST001').first()
    if not user:
        print("❌ User TEST001 not found. Register first!")
        exit(1)
    
    # Get class settings
    settings = get_class_settings()
    class_start_str = settings['class_start_time']
    late_threshold = settings['late_threshold_minutes']
    
    # Parse class start time
    time_parts = class_start_str.split(':')
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    second = int(time_parts[2]) if len(time_parts) > 2 else 0
    
    # Create entry time (simulate 5 minutes after class start = On Time)
    today = datetime.now().date()
    class_start = datetime.combine(today, dt_time(hour, minute, second))
    entry_time = class_start + timedelta(minutes=5)  # 5 min after = On Time
    
    # Calculate if late
    late_limit = class_start + timedelta(minutes=late_threshold)
    is_late = 1 if entry_time > late_limit else 0
    
    # Create attendance record
    attendance = Attendance(
        user_id=user.id,
        user_name=user.name,
        user_usn=user.usn,
        entry_time=entry_time,
        date=today.strftime('%Y-%m-%d'),
        is_late=is_late,
        camera_id='simulated_camera',
        class_start_time=class_start
    )
    session.add(attendance)
    session.commit()
    
    status = "Late" if is_late else "On Time"
    print(f"✅ Attendance created:")
    print(f"   Student: {user.name} ({user.usn})")
    print(f"   Entry Time: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Class Start: {class_start.strftime('%H:%M:%S')}")
    print(f"   Status: {status}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
EOF
```

**Step 4: Verify in Flutter App**
- Open Flutter app
- Login with USN: `TEST001`
- See attendance record in dashboard

**Step 5: Verify in Admin Panel**
- Open admin panel
- See attendance record in table
- Check analytics dashboard

---

## 🔍 Verification Checklist

After simulation, verify:

- [ ] Backend is running (`http://localhost:5001/api/status`)
- [ ] Class settings configured (Settings page)
- [ ] Student registered (Users list or Approvals)
- [ ] Student approved (status = "approved")
- [ ] Attendance record created (Attendance table)
- [ ] Record visible in Flutter app
- [ ] Record visible in admin panel
- [ ] Late/On Time status correct
- [ ] Analytics shows correct data

---

## 🐛 Troubleshooting

**Backend not starting:**
```bash
# Check if port 5001 is in use
lsof -i :5001

# Kill process if needed
kill -9 <PID>
```

**Flutter app can't connect:**
- Check `api_service.dart` baseUrl
- Ensure backend is running
- Check network/firewall

**No attendance records:**
- Verify student is approved
- Check database: `sqlite3 attendance.db "SELECT * FROM attendance;"`
- Verify record was created

**Database location:**
```bash
# Find database file
find . -name "attendance.db" -type f

# Check database contents
sqlite3 attendance.db ".tables"
sqlite3 attendance.db "SELECT COUNT(*) FROM users;"
sqlite3 attendance.db "SELECT COUNT(*) FROM attendance;"
```

---

## 📊 Database Inspection

```bash
# View all users
sqlite3 attendance.db "SELECT id, name, usn, status FROM users;"

# View all attendance
sqlite3 attendance.db "SELECT id, user_name, user_usn, entry_time, is_late FROM attendance ORDER BY entry_time DESC LIMIT 10;"

# View class settings
sqlite3 attendance.db "SELECT * FROM class_settings;"
```

---

## 🎯 Quick Test Commands

```bash
# Test 1: Check backend
curl http://localhost:5001/api/status

# Test 2: List students (requires login, so use browser)
# Open: http://localhost:5001/api/users

# Test 3: Check class settings (requires login)
# Open: http://localhost:5001/api/class-time

# Test 4: View attendance (requires login)
# Open: http://localhost:5001/api/attendance
```

---

## ✅ Success Indicators

**Complete Flow Working If:**
1. ✅ Backend starts without errors
2. ✅ Admin can login and access dashboard
3. ✅ Student can register via Flutter app
4. ✅ Admin can approve student
5. ✅ Attendance record can be created (simulated)
6. ✅ Student sees record in Flutter app
7. ✅ Admin sees record in web panel
8. ✅ Late/On Time status is correct
9. ✅ Analytics show correct data
10. ✅ Reports can be exported

If all 10 checkboxes are ✅, your complete flow is working!


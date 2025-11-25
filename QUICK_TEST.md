# Quick Test Guide - Complete Flow

## 🚀 5-Minute Complete Flow Test

### Step 1: Start Backend (Terminal 1)
```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py
```
✅ Wait for: `Running on http://127.0.0.1:5001`

### Step 2: Run Complete Flow Test (Terminal 2)
```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 test_complete_flow.py
```

This will:
- ✅ Check backend status
- ✅ List registered students
- ✅ List attendance records
- ✅ Simulate attendance for approved students

### Step 3: Register Student (Choose One)

**Option A: Flutter App**
```bash
cd flutter_app
flutter run
# Enter USN: TEST001 → Register with photos
```

**Option B: Admin Panel**
1. Open: `http://localhost:5001`
2. Login: `admin@gmail.com` / `admin`
3. Click "➕ Add User"
4. Enter: Name `Test Student`, USN `TEST001`
5. Capture photo → Add User

### Step 4: Approve Student (If Registered via Flutter)
1. Admin panel → "✅ Approvals"
2. Click "✅ Approve" for TEST001

### Step 5: Simulate Attendance
```bash
python3 test_complete_flow.py
# This will automatically simulate attendance for approved students
```

### Step 6: Verify Results

**In Flutter App:**
- Login with USN: `TEST001`
- See attendance record in dashboard
- Check Late/On Time status

**In Admin Panel:**
- See attendance record in table
- Check analytics dashboard
- Export report (Excel/PDF)

---

## ✅ Success Checklist

- [ ] Backend running (port 5001)
- [ ] Student registered (USN: TEST001)
- [ ] Student approved (status: approved)
- [ ] Attendance record created (simulated)
- [ ] Record visible in Flutter app
- [ ] Record visible in admin panel
- [ ] Late/On Time status correct

---

## 🐛 Common Issues

**Flutter app won't run:**
```bash
cd flutter_app
flutter clean
flutter pub get
flutter run
```

**Backend won't start:**
```bash
# Check if port in use
lsof -i :5001
# Kill if needed: kill -9 <PID>
```

**No students found:**
- Register student first (Step 3)
- Check: `python3 test_complete_flow.py` shows students

**Attendance not showing:**
- Run simulation: `python3 test_complete_flow.py`
- Check database: `sqlite3 attendance.db "SELECT * FROM attendance;"`

---

## 📊 Database Location

**Database File:**
```
/Users/sajid/Downloads/Code/Mini/Project/attendance.db
```

**View Database:**
```bash
sqlite3 attendance.db
.tables
SELECT * FROM users;
SELECT * FROM attendance;
SELECT * FROM class_settings;
.quit
```

---

## 🎯 Complete Flow Status

Run this to check everything:
```bash
python3 test_complete_flow.py
```

If all checks pass ✅, your complete flow is working!


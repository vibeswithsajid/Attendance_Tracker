# 🚀 Quick Start - Complete Flow Simulation

## ✅ Status: All Syntax Errors Fixed!

The backend is now ready. Follow these steps to simulate the complete flow:

---

## Step 1: Start Backend (Terminal 1)

```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py
```

**Wait for:** `Running on http://127.0.0.1:5001`

---

## Step 2: Check System Status (Terminal 2)

```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 test_complete_flow.py
```

**Expected Output:**
- ✅ Database connected
- ✅ Backend running
- ⚠️  No students yet (normal for first run)

---

## Step 3: Register a Student

### Option A: Via Admin Panel (Fastest)

1. Open browser: `http://localhost:5001`
2. Login: `admin@gmail.com` / `admin`
3. Click **"➕ Add User"**
4. Enter:
   - Name: `Test Student`
   - USN: `TEST001`
5. Capture/upload photo
6. Click **"Add User"**

✅ Student registered and auto-approved!

### Option B: Via Flutter App

1. **Start Flutter App:**
   ```bash
   cd flutter_app
   flutter run
   ```

2. **Register:**
   - Enter USN: `TEST001`
   - Click "Login"
   - App shows Registration screen
   - Enter Name: `Test Student`
   - Take/Select 2-5 photos
   - Click "Register"

3. **Approve in Admin Panel:**
   - Open: `http://localhost:5001`
   - Click **"✅ Approvals"**
   - Click **"✅ Approve"** for TEST001

---

## Step 4: Simulate Attendance

Run the test script again - it will automatically simulate attendance for approved students:

```bash
python3 test_complete_flow.py
```

**This will:**
- ✅ Find approved students
- ✅ Create attendance records (On Time and Late)
- ✅ Show results

---

## Step 5: View Results

### In Flutter App:
1. Open Flutter app
2. Login with USN: `TEST001`
3. See attendance records in dashboard
4. Check Late/On Time status

### In Admin Panel:
1. Open: `http://localhost:5001`
2. See attendance records in table
3. Check analytics dashboard
4. Export reports (Excel/PDF)

---

## 🎯 Complete Flow Checklist

- [ ] Backend running (port 5001)
- [ ] Student registered (USN: TEST001)
- [ ] Student approved (if registered via Flutter)
- [ ] Attendance records created (via test script)
- [ ] Records visible in Flutter app
- [ ] Records visible in admin panel
- [ ] Late/On Time status correct

---

## 🐛 Troubleshooting

**Backend won't start:**
```bash
# Check if port in use
lsof -i :5001
# Kill if needed: kill -9 <PID>
```

**Flutter app can't connect:**
- Check `flutter_app/lib/services/api_service.dart` - baseUrl should be `http://localhost:5001`
- For Android emulator, use `http://10.0.2.2:5001`
- For physical device, use your Mac's IP: `http://192.168.x.x:5001`

**No students found:**
- Register student first (Step 3)
- Check: `python3 test_complete_flow.py` shows students

**Migration warning:**
- The transaction warning is harmless - database still works
- Can be ignored for now

---

## 📊 Database Location

```bash
# View database
sqlite3 attendance.db

# Check tables
.tables

# View users
SELECT id, name, usn, status FROM users;

# View attendance
SELECT id, user_name, user_usn, entry_time, is_late FROM attendance;

# View class settings
SELECT * FROM class_settings;

.quit
```

---

## ✅ Success!

If all checklist items are ✅, your complete flow is working perfectly!

**Next Steps:**
- Test with real camera (see `CAMERA_SETUP_GUIDE.md`)
- Add more students
- Test different scenarios (early entry, late entry, etc.)
- Export reports and verify data

---

## 📚 Documentation

- **`SIMULATION_GUIDE.md`** - Detailed simulation guide
- **`QUICK_TEST.md`** - Quick test commands
- **`COMPLETE_WORKFLOW.md`** - End-to-end workflow
- **`CAMERA_SETUP_GUIDE.md`** - Camera setup and simulation
- **`SYSTEM_OVERVIEW.md`** - Complete API documentation


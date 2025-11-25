# 📱 Build APK & Test on Physical Device with Ngrok

## Step 1: Install Ngrok

### On macOS:
```bash
# Using Homebrew (recommended)
brew install ngrok/ngrok/ngrok

# Or download from https://ngrok.com/download
```

### Verify Installation:
```bash
ngrok version
```

## Step 2: Sign Up for Ngrok (Free)

1. Go to https://ngrok.com/
2. Sign up for a free account
3. Get your authtoken from the dashboard
4. Configure ngrok:
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

## Step 3: Start Your Backend Server

```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py
```

**Keep this terminal open!** The server should be running on `http://localhost:5001`

## Step 4: Start Ngrok Tunnel

**Open a NEW terminal window** and run:

```bash
ngrok http 5001
```

You'll see output like:
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:5001
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok-free.app`)

## Step 5: Update Flutter App API URL

### Option A: Quick Test (Temporary)
Edit `flutter_app/lib/services/api_service.dart`:

```dart
class ApiService {
  // Replace with your ngrok URL
  static const String baseUrl = 'https://abc123.ngrok-free.app';  // <-- YOUR NGROK URL HERE
  
  // ... rest of the code
}
```

### Option B: Environment-Based (Recommended)
Create a config file that switches based on build:

1. Create `flutter_app/lib/config/api_config.dart`:
```dart
class ApiConfig {
  // Change this to your ngrok URL when testing on physical device
  static const String baseUrl = 'https://abc123.ngrok-free.app';
  
  // For local testing (emulator/simulator):
  // static const String baseUrl = 'http://localhost:5001';
  
  // For Android emulator:
  // static const String baseUrl = 'http://10.0.2.2:5001';
}
```

2. Update `api_service.dart`:
```dart
import 'config/api_config.dart';

class ApiService {
  static const String baseUrl = ApiConfig.baseUrl;
  // ... rest of the code
}
```

## Step 6: Build APK

### Debug APK (Quick Testing):
```bash
cd flutter_app
flutter build apk --debug
```

The APK will be at: `flutter_app/build/app/outputs/flutter-apk/app-debug.apk`

### Release APK (Production):
```bash
cd flutter_app
flutter build apk --release
```

The APK will be at: `flutter_app/build/app/outputs/flutter-apk/app-release.apk`

## Step 7: Install APK on Physical Device

### Method 1: Using ADB (Android Debug Bridge)
```bash
# Connect your phone via USB
# Enable USB Debugging on your phone

# Install the APK
adb install flutter_app/build/app/outputs/flutter-apk/app-debug.apk
```

### Method 2: Transfer and Install Manually
1. Copy the APK file to your phone (via USB, email, or cloud storage)
2. On your phone, enable "Install from Unknown Sources" in Settings
3. Open the APK file and install

### Method 3: Using Flutter Install
```bash
flutter install
# (Make sure your device is connected and recognized)
```

## Step 8: Test the App

1. **Open the app** on your physical device
2. **Check connection**: The app should connect to your backend via ngrok
3. **Test features**:
   - Login/Registration
   - View attendance
   - All API calls should work

## 🔧 Troubleshooting

### Ngrok Issues:

**"ngrok: command not found"**
- Make sure ngrok is installed and in your PATH
- Try: `brew install ngrok/ngrok/ngrok`

**"ERR_NGROK_3200" or "Tunnel not found"**
- Make sure your backend is running on port 5001
- Check ngrok is forwarding to the correct port
- Restart ngrok: Press `Ctrl+C` and run `ngrok http 5001` again

**"Connection refused"**
- Verify backend is running: `curl http://localhost:5001/api/status`
- Check ngrok URL is correct in Flutter app
- Make sure ngrok tunnel is active (check ngrok terminal)

### Flutter Build Issues:

**"Gradle build failed"**
```bash
cd flutter_app/android
./gradlew clean
cd ..
flutter clean
flutter pub get
flutter build apk
```

**"SDK location not found"**
- Make sure Android SDK is installed
- Set `ANDROID_HOME` environment variable

### Connection Issues:

**App can't connect to backend**
1. Verify ngrok is running and shows "Online" status
2. Test ngrok URL in browser: `https://your-ngrok-url.ngrok-free.app/api/status`
3. Check Flutter app's `baseUrl` matches ngrok URL exactly
4. Make sure your phone has internet connection
5. Try accessing ngrok URL in phone's browser first

**CORS Errors**
- Backend already has CORS enabled, but if issues persist:
- Check `app.py` has `CORS(app)` configured

## 📝 Quick Reference

### Start Everything:
```bash
# Terminal 1: Backend
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py

# Terminal 2: Ngrok
ngrok http 5001

# Terminal 3: Build APK
cd flutter_app
flutter build apk --debug
```

### Update API URL:
1. Get ngrok URL from Terminal 2
2. Update `flutter_app/lib/services/api_service.dart`
3. Rebuild APK: `flutter build apk --debug`

### Test Connection:
```bash
# Test ngrok URL (replace with your URL)
curl https://abc123.ngrok-free.app/api/status
```

## 🎯 Complete Workflow

1. ✅ Start backend: `python3 app.py`
2. ✅ Start ngrok: `ngrok http 5001`
3. ✅ Copy ngrok HTTPS URL
4. ✅ Update Flutter `api_service.dart` with ngrok URL
5. ✅ Build APK: `flutter build apk --debug`
6. ✅ Install APK on phone
7. ✅ Test app - should connect via ngrok!

## 💡 Pro Tips

- **Keep ngrok running** while testing - if you restart it, you'll get a new URL
- **Use ngrok's free plan** - gives you a random URL each time (good for testing)
- **For production**, consider ngrok paid plan for fixed domain
- **Alternative**: Use your computer's IP address if on same WiFi network
  - Find IP: `ifconfig | grep "inet "` (macOS/Linux)
  - Use: `http://YOUR_IP:5001` in Flutter app
  - No ngrok needed, but only works on same network

## 🔐 Security Note

- Ngrok free URLs are public - anyone with the URL can access your backend
- **Don't use in production** without proper authentication
- For testing, this is fine
- Consider adding IP whitelisting or additional security for production


# 🔗 Ngrok Setup Complete!

## ✅ Your Ngrok URL is Configured

Your Flutter app is now configured to use:
```
https://geodynamical-knobbiest-annika.ngrok-free.dev
```

## 📱 How to Use

### 1. **Keep Ngrok Running**
Make sure ngrok is running in a terminal:
```bash
ngrok http 5001
```

**Important**: Keep this terminal open while testing!

### 2. **Keep Backend Running**
In another terminal, keep your backend running:
```bash
cd /Users/sajid/Downloads/Code/Mini/Project
python3 app.py
```

### 3. **Test the Connection**

#### Test in Browser:
Open: `https://geodynamical-knobbiest-annika.ngrok-free.dev/api/status`

Should return JSON with system status.

#### Test in Flutter App:
1. Build and run the Flutter app
2. Try registration or login
3. Should connect successfully!

## 🔄 Switching Between Ngrok and Local

### For Physical Device (Current Setup):
```dart
static const String baseUrl = 'https://geodynamical-knobbiest-annika.ngrok-free.dev';
```

### For Android Emulator:
```dart
static const String baseUrl = 'http://10.0.2.2:5001';
```

### For iOS Simulator:
```dart
static const String baseUrl = 'http://localhost:5001';
```

**Edit**: `flutter_app/lib/services/api_service.dart` (line 12)

## ⚠️ Important Notes

1. **Ngrok URL Changes**: If you restart ngrok, you'll get a new URL. Update it in `api_service.dart`

2. **Ngrok Free Plan**: 
   - URL changes each time you restart
   - Has request limits
   - Good for testing

3. **Keep Both Running**:
   - Backend (`python3 app.py`)
   - Ngrok (`ngrok http 5001`)

4. **Test Connection First**:
   ```bash
   curl https://geodynamical-knobbiest-annika.ngrok-free.dev/api/status
   ```

## 🚀 Build APK with Ngrok

1. **Make sure ngrok is running** (get the URL)
2. **Update `api_service.dart`** with ngrok URL (already done!)
3. **Build APK**:
   ```bash
   cd flutter_app
   flutter build apk --debug
   ```
4. **Install on device**:
   ```bash
   adb install build/app/outputs/flutter-apk/app-debug.apk
   ```

## ✅ Current Status

- ✅ Ngrok URL configured: `https://geodynamical-knobbiest-annika.ngrok-free.dev`
- ✅ Flutter app will use this URL
- ✅ Ready for physical device testing

**Just make sure ngrok and backend are both running!**


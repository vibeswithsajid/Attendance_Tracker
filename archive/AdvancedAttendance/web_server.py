import cv2
import time
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from core.utils import load_config, load_camera_config, setup_logging, draw_overlays
from core.database import FaceDatabase
from core.face_detection import FaceDetector
from core.camera_manager import CameraManager
from core.attendance import AttendanceTracker
from core.alert_system import AlertSystem
from loguru import logger

# Initialize App
app = FastAPI(title="InsightFace Attendance System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & Templates
app.mount("/static", StaticFiles(directory="web"), name="static")
templates = Jinja2Templates(directory="web")

# Global System State
class SystemState:
    def __init__(self):
        self.config = load_config("config/config.yaml")
        self.cam_config = load_camera_config("config/camera_config.yaml")
        setup_logging(self.config['directories']['logs'])
        
        self.db = FaceDatabase()
        self.detector = FaceDetector(self.config)
        
        # Load known faces
        known_faces = self.db.get_known_faces()
        self.detector.load_known_faces(known_faces)
        
        self.tracker = AttendanceTracker(self.db, self.config)
        self.alert_system = AlertSystem(self.config)
        self.camera_manager = CameraManager(self.cam_config)
        
        # Start Systems
        self.camera_manager.start_all()
        self.alert_system.start()

state = SystemState()

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Routes
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/status")
async def get_status():
    cameras = state.camera_manager.get_active_cameras()
    return {
        "cameras": len(cameras),
        "active_sessions": len(state.tracker.active_sessions),
        "known_faces": len(state.detector.known_faces)
    }

def generate_frames(cam_id):
    while True:
        cameras = state.camera_manager.get_active_cameras()
        if cam_id not in cameras:
            time.sleep(1)
            continue
            
        frame = cameras[cam_id].get_frame()
        if frame is None:
            time.sleep(0.01)
            continue
            
        # Process (Optional: We could skip processing here to save CPU if just viewing)
        # But we want to see boxes.
        # Note: Processing every frame in the stream loop might be heavy if multiple clients connect.
        # Ideally, processing happens in a background thread (like VideoThread in main.py)
        # and this just streams the result.
        # For now, let's do lightweight processing or just raw frame.
        # Let's do raw frame + simple detection if needed.
        # BETTER: Use the processed frame from a central processing loop.
        # But we don't have a central loop here yet.
        
        # Let's just stream the raw frame for now to ensure speed, 
        # or do detection if we want.
        # Let's do detection.
        faces = state.detector.process_frame(frame)
        
        # Update Tracker
        for face in faces:
            if face['name'] != "Unknown":
                state.tracker.process_detection(face, cam_id, cameras[cam_id].name)
                # We could trigger alerts here too, but be careful of duplicates
                # state.alert_system.trigger_alert(...)
        
        draw_overlays(frame, faces)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/stream/{cam_id}")
async def video_feed(cam_id: str):
    return StreamingResponse(generate_frames(cam_id), 
                             media_type="multipart/x-mixed-replace; boundary=frame")

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background Task for Timeouts
@app.on_event("startup")
async def startup_event():
    async def check_timeouts_loop():
        while True:
            state.tracker.check_timeouts()
            await asyncio.sleep(1)
            
    asyncio.create_task(check_timeouts_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

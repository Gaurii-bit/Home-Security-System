import cv2
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from security_system import IntelligentSecuritySystem
import threading
import time
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Intelligent Home Security System API")

# Allow CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Security System
print("Starting Security System in API Mode...")
system = IntelligentSecuritySystem()

# Global variables for camera stream
camera = None
output_frame = None
lock = threading.Lock()

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    return camera

def capture_frames():
    """Background thread to capture and process frames"""
    global output_frame, lock
    cap = get_camera()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
            
        # Process frame
        result = system.process_frame(frame)
        
        # Save output frame
        with lock:
            if 'annotated_frame' in result:
                output_frame = result['annotated_frame'].copy()
            else:
                output_frame = frame.copy()

# Start background thread for frame processing
thread = threading.Thread(target=capture_frames, daemon=True)
thread.start()

def generate_video():
    """Generator for MJPEG video stream"""
    global output_frame, lock
    
    while True:
        with lock:
            if output_frame is None:
                continue
            
            # Encode frame to JPEG
            ret, encoded_image = cv2.imencode(".jpg", output_frame)
            if not ret:
                continue
                
        # Yield multipart response
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
               bytearray(encoded_image) + b'\r\n')
        
        # Limit frame rate slightly to save CPU if needed
        time.sleep(0.03)

# Add custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@app.get("/video_feed")
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return StreamingResponse(generate_video(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/status")
def get_status():
    """Get system health and status metrics"""
    status = system.get_system_status()
    # Convert datetime to string for JSON serialization
    status_json = json.loads(json.dumps(status, cls=DateTimeEncoder))
    return status_json

@app.get("/api/logs")
def get_logs():
    """Get recent security event logs"""
    # Exclude _id to make it JSON serializable without BSON
    logs = list(system.db.db.logs.find({"event_type": "face_detection"}, {"_id": 0}).sort("timestamp", -1).limit(20))
    # Convert datetimes
    logs_json = json.loads(json.dumps(logs, cls=DateTimeEncoder))
    return logs_json

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup resources on shutdown"""
    global camera
    if camera:
        camera.release()
    system.cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

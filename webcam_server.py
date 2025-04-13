# Modified webcam_server.py to detect and use external USB camera
import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

def identify_cameras():
    """Identify all available cameras and their characteristics"""
    camera_info = []
    
    for index in range(10):  # Try indices 0-9
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Try to read a frame
            ret, frame = cap.read()
            if ret:
                # Get camera properties
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                
                info = {
                    "index": index,
                    "resolution": f"{width}x{height}",
                    "frame": frame  # Store a sample frame
                }
                camera_info.append(info)
                print(f"Camera {index}: {width}x{height} resolution")
            cap.release()
    
    return camera_info

# Identify all cameras
cameras = identify_cameras()
if not cameras:
    print("No cameras found!")
    exit()

# List all available cameras
print("\nAvailable cameras:")
for cam in cameras:
    print(f"Index {cam['index']}: {cam['resolution']}")

# If multiple cameras are available, try to determine which is external
camera_index = None
if len(cameras) > 1:
    print("\nMultiple cameras detected. The external USB camera is likely NOT index 0.")
    try:
        camera_index = int(input("Enter the index of the external USB camera (usually 1 or higher): "))
        if camera_index not in [cam["index"] for cam in cameras]:
            print(f"No camera with index {camera_index} found.")
            camera_index = None
    except ValueError:
        print("Invalid input. Using first available camera.")
        camera_index = cameras[0]["index"]
else:
    camera_index = cameras[0]["index"]

if camera_index is None:
    print("Using first available camera (index 0)")
    camera_index = 0

print(f"\nUsing camera at index {camera_index}")

# Initialize the selected camera
cap = cv2.VideoCapture(camera_index)
if not cap.isOpened():
    print(f"Failed to open camera at index {camera_index}. Exiting.")
    exit()

class WebcamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/still'):
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                self.send_error(500)
                return
                
            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', len(frame_bytes))
            self.end_headers()
            self.wfile.write(frame_bytes)
        elif self.path.startswith('/video'):
            # Simple HTML page that shows the video feed
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html><body>
            <h1>Webcam Feed</h1>
            <img src="/still" id="feed" />
            <script>
                setInterval(function() {
                    document.getElementById('feed').src = '/still?' + new Date().getTime();
                }, 100);
            </script>
            </body></html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_error(404)
    
    # This makes the server more responsive
    def log_message(self, format, *args):
        return
            
# Start server
server = HTTPServer(('0.0.0.0', 8000), WebcamHandler)
print("\nWebcam server started at http://localhost:8000")
print("Access video feed at http://localhost:8000/video")
print("Access still images at http://localhost:8000/still")
print("Press Ctrl+C to stop server")

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    cap.release()
    server.server_close()
    print("Server stopped")
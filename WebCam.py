import cv2
import os
import time
import json
import numpy as np
import matplotlib.pyplot as plt
import threading
import requests
import io
from PIL import Image
from science_jubilee.tools.Tool import Tool, requires_active_tool

def get_windows_ip():
    import subprocess
    return subprocess.check_output("cat /etc/resolv.conf | grep nameserver | awk '{print $2}'", shell=True).decode().strip()


class WebCam(Tool):
    def __init__(self, index, name, config_file, path=None):
        """Initialize the WebCam object.

        :param index: The tool index of the webcam
        :type index: int
        :param name: The name associated with the webcam
        :type name: str
        :param config_file: Path to the configuration JSON file
        :type config_file: str
        :param path: The path to the configuration file directory, defaults to the 'configs' folder in the same directory as WebCam.py
        :type path: str, optional
        """
        self.index = index
        self.name = name
        self.is_active_tool = False

        # Set the default path to the 'configs' folder in the same directory as WebCam.py
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "configs")

        # Load configuration from the JSON file
        config_path = os.path.join(path, config_file)
        with open(config_path, "r") as f:
            config = json.load(f)

        self.camera_index = config.get("camera_index", 0)
        self.output_dir = config.get("output_dir", "camera_output")
        self.focus_height = config.get("focus_height", 100)
        
        # Set up the webcam bridge connection details
        self.windows_ip = get_windows_ip()
        self.port = config.get("port", 8000)
        self.still_url = f"http://{self.windows_ip}:{self.port}/still"
        self.video_url = f"http://{self.windows_ip}:{self.port}/video"
        
        # Create mocked camera object to maintain compatibility
        self.camera = self._create_mock_camera()

        # Create the output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Autofocus capabilities may not be available through a bridge
        self.has_autofocus = False
        self.autofocus_enabled = False

    def _create_mock_camera(self):
        """Create a mock camera object with methods that will be called"""
        class MockCamera:
            def __init__(self, parent):
                self.parent = parent
                
            def read(self):
                """Get a frame from the webcam bridge"""
                try:
                    response = requests.get(self.parent.still_url, timeout=5)
                    if response.status_code == 200:
                        # Convert the image data to a numpy array
                        img_array = np.frombuffer(response.content, dtype=np.uint8)
                        frame = cv2.imdecode(img_array, -1)
                        return True, frame
                    else:
                        print(f"Failed to get image: {response.status_code}")
                        return False, None
                except Exception as e:
                    print(f"Error getting frame from webcam bridge: {e}")
                    return False, None
                    
            def release(self):
                """Mock release method"""
                pass
                
            def get(self, prop):
                """Mock property getter"""
                if prop == cv2.CAP_PROP_FRAME_WIDTH:
                    return 640  # Default width
                elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
                    return 480  # Default height
                return 0
                
            def set(self, prop, value):
                """Mock property setter - will always return True but not do anything"""
                return True
                
        return MockCamera(self)

    @requires_active_tool
    def take_picture(self, filename="image.jpg"):
        """Capture a picture and save it to the output directory."""
        ret, frame = self.camera.read()
        if ret:
            filepath = os.path.join(self.output_dir, filename)
            cv2.imwrite(filepath, frame)
            print(f"Picture saved to {filepath}")
            return filepath
        else:
            print("Failed to capture image.")
            return None

    @requires_active_tool
    def record_video(self, filename="video.avi", duration=10):
        """Record a video without displaying the preview window.

        :param filename: Name of the video file
        :type filename: str
        :param duration: Duration of the video in seconds
        :type duration: int
        """
        filepath = os.path.join(self.output_dir, filename)
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fps = 20.0
        frame_size = (
            int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        out = cv2.VideoWriter(filepath, fourcc, fps, frame_size)

        print(f"Recording video for {duration} seconds...")
        print(f"You can view the feed at: http://{self.windows_ip}:{self.port}/video")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            ret, frame = self.camera.read()
            if ret:
                out.write(frame)
                # Remove the cv2.imshow call that was causing problems
            else:
                print("Failed to capture frame.")
                break

        out.release()
        # Remove cv2.destroyAllWindows() call
        print(f"Video saved to {filepath}")
        return filepath

    @requires_active_tool
    def record_video_async(self, filename="async_video.avi", duration=10):
        """Record a video asynchronously in a separate thread.

        :param filename: Name of the video file
        :type filename: str
        :param duration: Duration of the video in seconds
        :type duration: int
        """
        self.stop_recording_flag = False  # Flag to stop recording early
        self.video_thread = threading.Thread(target=self._record_video, args=(filename, duration))
        self.video_thread.start()
        print(f"Started asynchronous video recording for {duration} seconds")
        print(f"You can view the feed at: http://{self.windows_ip}:{self.port}/video")

    def _record_video(self, filename, duration):
        """Internal method to record a video without using GUI components."""
        filepath = os.path.join(self.output_dir, filename)
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fps = 20.0
        frame_size = (
            int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        out = cv2.VideoWriter(filepath, fourcc, fps, frame_size)

        print(f"Recording video asynchronously for {duration} seconds...")
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.stop_recording_flag:
                print("Recording stopped early.")
                break

            ret, frame = self.camera.read()
            if ret:
                out.write(frame)
                # Removed cv2.imshow call
            else:
                print("Failed to capture frame.")
                break

        out.release()
        # Removed cv2.destroyAllWindows call
        print(f"Video saved to {filepath}")

    def stop_video_recording(self):
        """Stop the asynchronous video recording."""
        if hasattr(self, "stop_recording_flag"):
            self.stop_recording_flag = True
        if hasattr(self, "video_thread"):
            self.video_thread.join()  # Wait for the thread to finish
            print("Video recording thread stopped.")



        out.release()
        cv2.destroyAllWindows()
        print(f"Video saved to {filepath}")
        return filepath
    
    @requires_active_tool
    def preview(self):
        """Preview the camera feed via HTTP instead of direct display."""
        print(f"Camera preview available at: http://{self.windows_ip}:{self.port}/video")
        print("Open this URL in your browser to see the preview.")
        print("Press Enter to exit preview mode...")
        input()  # Just wait for user input to exit


    def view_image(self, filepath):
        """View an image from the specified file path."""
        image = cv2.imread(filepath)
        if image is not None:
            plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            plt.axis("off")
            plt.show()
        else:
            print(f"Failed to load image from {filepath}")

    def release(self):
        """Release the camera resource."""
        self.camera.release()
        cv2.destroyAllWindows()

    def set_manual_focus(self, focus_value):
        """Set manual focus value if supported by the camera.
        
        :param focus_value: Focus value (typically 0-255 for most webcams)
        :type focus_value: int
        :return: Success status
        :rtype: bool
        """
        if not self.has_autofocus:
            print("This camera doesn't support focus control.")
            return False
            
        try:
            # First disable autofocus
            success = self.disable_auto_focus()
            if not success:
                return False
                
            # Then set the focus value
            success = self.camera.set(cv2.CAP_PROP_FOCUS, focus_value)
            if success:
                print(f"Manual focus set to {focus_value}")
                return True
            else:
                print("Failed to set manual focus value")
                return False
        except Exception as e:
            print(f"Error setting manual focus: {e}")
            return False

    def enable_auto_focus(self):
        """Enable auto-focus if supported by the camera.
        
        :return: Success status
        :rtype: bool
        """
        if not self.has_autofocus:
            print("Auto-focus is not supported on this camera.")
            return False
            
        try:
            success = self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            if success:
                self.autofocus_enabled = True
                print("Auto-focus enabled.")
                return True
            else:
                print("Failed to enable auto-focus.")
                return False
        except Exception as e:
            print(f"Error enabling autofocus: {e}")
            return False

    def disable_auto_focus(self):
        """Disable auto-focus if supported by the camera.
        
        :return: Success status
        :rtype: bool
        """
        if not self.has_autofocus:
            print("Auto-focus is not supported on this camera.")
            return False
            
        try:
            success = self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            if success:
                self.autofocus_enabled = False
                print("Auto-focus disabled.")
                return True
            else:
                print("Failed to disable auto-focus.")
                return False
        except Exception as e:
            print(f"Error disabling autofocus: {e}")
            return False

    def is_auto_focus_enabled(self):
        """Check if auto-focus is enabled.
        
        :return: True if enabled, False if disabled, None if not supported
        :rtype: bool or None
        """
        if not self.has_autofocus:
            print("Auto-focus is not supported on this camera.")
            return None
            
        try:
            status = bool(self.camera.get(cv2.CAP_PROP_AUTOFOCUS))
            self.autofocus_enabled = status  # Update stored state
            print(f"Auto-focus is {'enabled' if status else 'disabled'}.")
            return status
        except Exception as e:
            print(f"Error checking autofocus status: {e}")
            return self.autofocus_enabled  # Return last known state
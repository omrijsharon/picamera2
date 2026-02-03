#!/usr/bin/python3

"""
ePTZ with Object Tracking Example

This example demonstrates how to use ePTZ to follow a detected object.
It simulates object detection and automatically adjusts the crop region
to keep the object centered and properly framed.

This technique is useful for:
- Security cameras tracking people or vehicles
- Sports broadcasting following athletes
- Wildlife cameras tracking animals
- Video conferencing following speakers

Note: This example uses simulated object detection. In a real application,
you would integrate with actual object detection (OpenCV, TensorFlow, etc.)
"""

import time
import math
from picamera2_contrib import Picamera2, Preview


class ObjectTracker:
    """Simulates object tracking and controls ePTZ to follow the object."""
    
    def __init__(self, picam2, output_size=(640, 480), target_zoom=2.0):
        """
        Initialize object tracker.
        
        Args:
            picam2: Picamera2 instance
            output_size: Output video resolution
            target_zoom: Zoom level to use when tracking (2.0 = 2x zoom)
        """
        self.picam2 = picam2
        self.output_size = output_size
        self.target_zoom = target_zoom
        
        # Get sensor dimensions
        self.sensor_width, self.sensor_height = picam2.camera_properties['PixelArraySize']
        
        # Current crop state
        self.current_pan_x = 0.5
        self.current_pan_y = 0.5
        self.current_zoom = 1.0
        
        # Tracking parameters
        self.smoothing = 0.3  # How quickly to adjust (0.1 = slow, 0.9 = fast)
        self.zoom_margin = 1.2  # How much extra space to leave around object
        
        print(f"Object Tracker initialized")
        print(f"Sensor: {self.sensor_width}x{self.sensor_height}")
        print(f"Output: {output_size[0]}x{output_size[1]}")
        print(f"Target zoom: {target_zoom}x")
    
    def calculate_crop(self, zoom, pan_x, pan_y):
        """Calculate ScalerCrop values."""
        output_width, output_height = self.output_size
        output_aspect = output_width / output_height
        
        # Calculate crop dimensions
        crop_width = int(self.sensor_width / zoom)
        crop_height = int(self.sensor_height / zoom)
        
        # Maintain aspect ratio
        if crop_width / crop_height > output_aspect:
            crop_width = int(crop_height * output_aspect)
        else:
            crop_height = int(crop_width / output_aspect)
        
        # Calculate position
        x = int((self.sensor_width - crop_width) * pan_x)
        y = int((self.sensor_height - crop_height) * pan_y)
        
        # Ensure even values
        x = (x // 2) * 2
        y = (y // 2) * 2
        crop_width = (crop_width // 2) * 2
        crop_height = (crop_height // 2) * 2
        
        # Clamp to valid range
        x = max(0, min(x, self.sensor_width - crop_width))
        y = max(0, min(y, self.sensor_height - crop_height))
        
        return (x, y, crop_width, crop_height)
    
    def track_object(self, object_x, object_y, object_width, object_height):
        """
        Update ePTZ to track an object.
        
        Args:
            object_x: Object center X in output coordinates (pixels)
            object_y: Object center Y in output coordinates (pixels)
            object_width: Object width in output coordinates (pixels)
            object_height: Object height in output coordinates (pixels)
        """
        output_width, output_height = self.output_size
        
        # Normalize object position to 0.0-1.0 range
        target_pan_x = object_x / output_width
        target_pan_y = object_y / output_height
        
        # Calculate desired zoom based on object size
        # Larger objects need less zoom, smaller objects need more zoom
        object_relative_width = object_width / output_width
        object_relative_height = object_height / output_height
        object_size = max(object_relative_width, object_relative_height)
        
        # Calculate zoom to keep object at reasonable size in frame
        if object_size > 0.01:  # Avoid division by zero
            desired_zoom = min(self.target_zoom, 1.0 / (object_size * self.zoom_margin))
            desired_zoom = max(1.0, min(desired_zoom, 6.0))  # Clamp zoom range
        else:
            desired_zoom = self.target_zoom
        
        # Smooth transitions
        self.current_pan_x += (target_pan_x - self.current_pan_x) * self.smoothing
        self.current_pan_y += (target_pan_y - self.current_pan_y) * self.smoothing
        self.current_zoom += (desired_zoom - self.current_zoom) * self.smoothing * 0.5
        
        # Apply crop
        crop = self.calculate_crop(self.current_zoom, self.current_pan_x, self.current_pan_y)
        self.picam2.set_controls({"ScalerCrop": crop})
        
        return crop


def simulate_moving_object(time_elapsed):
    """
    Simulate a moving object in the frame.
    Returns (center_x, center_y, width, height) in output coordinates.
    
    This simulates an object moving in a circular pattern.
    """
    # Circular motion parameters
    center_x = 320  # Center of 640x480 frame
    center_y = 240
    radius = 150  # Radius of circular path
    angular_speed = 0.5  # Radians per second
    
    # Calculate position on circular path
    angle = time_elapsed * angular_speed
    obj_x = center_x + radius * math.cos(angle)
    obj_y = center_y + radius * math.sin(angle)
    
    # Simulate varying object size (getting closer/farther)
    size_variation = 1.0 + 0.3 * math.sin(angle * 2)
    obj_width = 80 * size_variation
    obj_height = 120 * size_variation
    
    return (obj_x, obj_y, obj_width, obj_height)


def main():
    """Run the object tracking demo."""
    print("\n" + "="*60)
    print("ePTZ Object Tracking Demo")
    print("="*60)
    print("\nThis demo simulates an object moving in a circular pattern")
    print("and uses ePTZ to automatically track and frame it.")
    print("\nPress Ctrl+C to stop.\n")
    
    # Initialize camera
    picam2 = Picamera2()
    
    # Configure for 480p output
    output_size = (640, 480)
    config = picam2.create_video_configuration(
        main={"size": output_size, "format": "XRGB8888"}
    )
    
    picam2.configure(config)
    picam2.start_preview(Preview.QTGL)
    picam2.start()
    
    # Wait for camera to warm up
    time.sleep(2)
    
    # Initialize tracker
    tracker = ObjectTracker(picam2, output_size, target_zoom=2.5)
    
    # Start with full view
    crop = tracker.calculate_crop(1.0, 0.5, 0.5)
    picam2.set_controls({"ScalerCrop": crop})
    
    print("\nStarting tracking in 2 seconds...")
    time.sleep(2)
    
    try:
        start_time = time.time()
        frame_count = 0
        
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Simulate object detection
            obj_x, obj_y, obj_w, obj_h = simulate_moving_object(elapsed)
            
            # Track the object with ePTZ
            crop = tracker.track_object(obj_x, obj_y, obj_w, obj_h)
            
            # Print status every 30 frames
            if frame_count % 30 == 0:
                print(f"Time: {elapsed:5.1f}s | "
                      f"Object: ({obj_x:3.0f}, {obj_y:3.0f}) {obj_w:3.0f}x{obj_h:3.0f} | "
                      f"Zoom: {tracker.current_zoom:4.2f}x | "
                      f"Pan: ({tracker.current_pan_x:4.2f}, {tracker.current_pan_y:4.2f})")
            
            frame_count += 1
            
            # Small delay to simulate processing time
            time.sleep(0.033)  # ~30 fps
    
    except KeyboardInterrupt:
        print("\n\nStopping demo...")
    
    finally:
        picam2.stop()
        picam2.close()
        print("Demo finished.")


if __name__ == "__main__":
    main()

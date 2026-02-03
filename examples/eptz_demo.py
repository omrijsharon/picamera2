#!/usr/bin/python3

"""
Electronic Pan-Tilt-Zoom (ePTZ) Demo

This example demonstrates how to implement electronic pan, tilt, and zoom
using the ScalerCrop control. It allows you to:
- Use a high-resolution sensor (e.g., 4K) while outputting lower resolution video (e.g., 480p)
- Digitally zoom in and out (1x to 4x)
- Pan left/right and tilt up/down
- Smoothly transition between positions

Controls:
- Arrow keys: Pan and tilt
- + / -: Zoom in/out
- Home: Reset to center
- Q: Quit

This is useful for:
- Security cameras focusing on specific areas
- Video conferencing with digital PTZ
- Wildlife monitoring with remote control
- Extracting higher detail from specific regions
"""

import time
from picamera2_contrib import Picamera2, Preview

# Try to import keyboard library for controls
try:
    import readchar
    HAS_READCHAR = True
except ImportError:
    print("Install 'readchar' for keyboard controls: pip install readchar")
    HAS_READCHAR = False


class ePTZController:
    """Controller for electronic Pan-Tilt-Zoom operations."""
    
    def __init__(self, picam2, output_size=(640, 480)):
        """
        Initialize ePTZ controller.
        
        Args:
            picam2: Picamera2 instance
            output_size: Output video resolution (width, height)
        """
        self.picam2 = picam2
        self.output_size = output_size
        
        # Get sensor dimensions
        self.sensor_width, self.sensor_height = picam2.camera_properties['PixelArraySize']
        
        # Get min/max crop limits
        min_crop, max_crop, default_crop = picam2.camera_controls['ScalerCrop']
        self.max_crop = max_crop
        
        print(f"Sensor resolution: {self.sensor_width}x{self.sensor_height}")
        print(f"Output resolution: {output_size[0]}x{output_size[1]}")
        print(f"Max crop region: {max_crop}")
        
        # Current PTZ state
        self.zoom_factor = 1.0  # 1.0 = no zoom, 2.0 = 2x zoom, etc.
        self.pan_x = 0.5  # 0.0 = left, 0.5 = center, 1.0 = right
        self.pan_y = 0.5  # 0.0 = top, 0.5 = center, 1.0 = bottom
        
        # Limits
        self.min_zoom = 1.0
        self.max_zoom = 8.0  # Can be adjusted based on sensor
        
        # Step sizes for controls
        self.zoom_step = 0.2
        self.pan_step = 0.05
        
    def calculate_crop(self):
        """
        Calculate ScalerCrop values based on current PTZ state.
        
        Returns:
            Tuple of (x, y, width, height) for ScalerCrop
        """
        output_width, output_height = self.output_size
        
        # Calculate aspect ratio
        output_aspect = output_width / output_height
        sensor_aspect = self.sensor_width / self.sensor_height
        
        # Calculate crop dimensions based on zoom
        crop_width = int(self.sensor_width / self.zoom_factor)
        crop_height = int(self.sensor_height / self.zoom_factor)
        
        # Maintain aspect ratio of output
        if output_aspect > sensor_aspect:
            # Output is wider relative to sensor
            crop_height = int(crop_width / output_aspect)
        else:
            # Output is taller relative to sensor
            crop_width = int(crop_height * output_aspect)
        
        # Ensure crop doesn't exceed sensor bounds
        crop_width = min(crop_width, self.sensor_width)
        crop_height = min(crop_height, self.sensor_height)
        
        # Calculate position based on pan values
        max_x = self.sensor_width - crop_width
        max_y = self.sensor_height - crop_height
        
        x = int(max_x * self.pan_x)
        y = int(max_y * self.pan_y)
        
        # Ensure even values (required by hardware)
        x = (x // 2) * 2
        y = (y // 2) * 2
        crop_width = (crop_width // 2) * 2
        crop_height = (crop_height // 2) * 2
        
        # Clamp to valid range
        x = max(0, min(x, self.sensor_width - crop_width))
        y = max(0, min(y, self.sensor_height - crop_height))
        
        return (x, y, crop_width, crop_height)
    
    def apply_crop(self):
        """Apply the current crop settings to the camera."""
        crop = self.calculate_crop()
        self.picam2.set_controls({"ScalerCrop": crop})
        return crop
    
    def zoom_in(self):
        """Increase zoom (smaller crop region)."""
        self.zoom_factor = min(self.zoom_factor + self.zoom_step, self.max_zoom)
        return self.apply_crop()
    
    def zoom_out(self):
        """Decrease zoom (larger crop region)."""
        self.zoom_factor = max(self.zoom_factor - self.zoom_step, self.min_zoom)
        return self.apply_crop()
    
    def pan_left(self):
        """Pan left (move crop region left)."""
        self.pan_x = max(0.0, self.pan_x - self.pan_step)
        return self.apply_crop()
    
    def pan_right(self):
        """Pan right (move crop region right)."""
        self.pan_x = min(1.0, self.pan_x + self.pan_step)
        return self.apply_crop()
    
    def tilt_up(self):
        """Tilt up (move crop region up)."""
        self.pan_y = max(0.0, self.pan_y - self.pan_step)
        return self.apply_crop()
    
    def tilt_down(self):
        """Tilt down (move crop region down)."""
        self.pan_y = min(1.0, self.pan_y + self.pan_step)
        return self.apply_crop()
    
    def reset(self):
        """Reset to center position with no zoom."""
        self.zoom_factor = 1.0
        self.pan_x = 0.5
        self.pan_y = 0.5
        return self.apply_crop()
    
    def smooth_zoom_to(self, target_zoom, duration=1.0, steps=30):
        """
        Smoothly zoom to target zoom level.
        
        Args:
            target_zoom: Target zoom factor
            duration: Duration in seconds
            steps: Number of intermediate steps
        """
        target_zoom = max(self.min_zoom, min(target_zoom, self.max_zoom))
        start_zoom = self.zoom_factor
        
        for i in range(steps + 1):
            progress = i / steps
            self.zoom_factor = start_zoom + (target_zoom - start_zoom) * progress
            self.apply_crop()
            time.sleep(duration / steps)
    
    def smooth_pan_to(self, target_pan_x, target_pan_y, duration=1.0, steps=30):
        """
        Smoothly pan to target position.
        
        Args:
            target_pan_x: Target X position (0.0 to 1.0)
            target_pan_y: Target Y position (0.0 to 1.0)
            duration: Duration in seconds
            steps: Number of intermediate steps
        """
        target_pan_x = max(0.0, min(1.0, target_pan_x))
        target_pan_y = max(0.0, min(1.0, target_pan_y))
        
        start_pan_x = self.pan_x
        start_pan_y = self.pan_y
        
        for i in range(steps + 1):
            progress = i / steps
            self.pan_x = start_pan_x + (target_pan_x - start_pan_x) * progress
            self.pan_y = start_pan_y + (target_pan_y - start_pan_y) * progress
            self.apply_crop()
            time.sleep(duration / steps)
    
    def get_status(self):
        """Get current PTZ status as string."""
        crop = self.calculate_crop()
        return (f"Zoom: {self.zoom_factor:.1f}x | "
                f"Pan: {self.pan_x:.2f} | "
                f"Tilt: {self.pan_y:.2f} | "
                f"Crop: {crop[0]},{crop[1]} {crop[2]}x{crop[3]}")


def print_help():
    """Print help message."""
    print("\n" + "="*60)
    print("Electronic Pan-Tilt-Zoom (ePTZ) Demo")
    print("="*60)
    print("\nKeyboard Controls:")
    print("  Arrow Keys    - Pan and Tilt")
    print("  + / =         - Zoom In")
    print("  - / _         - Zoom Out")
    print("  h / Home      - Reset to center")
    print("  q / Esc       - Quit")
    print("\nPreset Positions (1-4):")
    print("  1 - Top Left Corner")
    print("  2 - Top Right Corner")
    print("  3 - Bottom Left Corner")
    print("  4 - Bottom Right Corner")
    print("  5 - Center with 2x Zoom")
    print("\n" + "="*60 + "\n")


def run_interactive_demo():
    """Run interactive ePTZ demo with keyboard controls."""
    if not HAS_READCHAR:
        print("Interactive mode requires 'readchar' library.")
        print("Install with: pip install readchar")
        return
    
    # Initialize camera
    picam2 = Picamera2()
    
    # Configure for 480p output (you can change this)
    output_size = (640, 480)
    config = picam2.create_video_configuration(
        main={"size": output_size, "format": "XRGB8888"}
    )
    
    picam2.configure(config)
    
    # Start preview
    picam2.start_preview(Preview.QTGL)
    picam2.start()
    
    # Wait for camera to warm up
    time.sleep(1)
    
    # Initialize ePTZ controller
    controller = ePTZController(picam2, output_size)
    controller.apply_crop()
    
    print_help()
    print(controller.get_status())
    
    try:
        while True:
            # Read key
            key = readchar.readkey()
            
            # Handle key presses
            if key in ('q', 'Q', readchar.key.ESC):
                break
            elif key == readchar.key.UP:
                controller.tilt_up()
                print(controller.get_status())
            elif key == readchar.key.DOWN:
                controller.tilt_down()
                print(controller.get_status())
            elif key == readchar.key.LEFT:
                controller.pan_left()
                print(controller.get_status())
            elif key == readchar.key.RIGHT:
                controller.pan_right()
                print(controller.get_status())
            elif key in ('+', '='):
                controller.zoom_in()
                print(controller.get_status())
            elif key in ('-', '_'):
                controller.zoom_out()
                print(controller.get_status())
            elif key in ('h', 'H', readchar.key.HOME):
                print("Resetting to center...")
                controller.reset()
                print(controller.get_status())
            elif key == '1':
                print("Moving to top-left corner...")
                controller.smooth_pan_to(0.2, 0.2, duration=0.5)
                print(controller.get_status())
            elif key == '2':
                print("Moving to top-right corner...")
                controller.smooth_pan_to(0.8, 0.2, duration=0.5)
                print(controller.get_status())
            elif key == '3':
                print("Moving to bottom-left corner...")
                controller.smooth_pan_to(0.2, 0.8, duration=0.5)
                print(controller.get_status())
            elif key == '4':
                print("Moving to bottom-right corner...")
                controller.smooth_pan_to(0.8, 0.8, duration=0.5)
                print(controller.get_status())
            elif key == '5':
                print("Zooming to center at 2x...")
                controller.smooth_pan_to(0.5, 0.5, duration=0.3)
                controller.smooth_zoom_to(2.0, duration=0.5)
                print(controller.get_status())
    
    finally:
        picam2.stop()
        picam2.close()
        print("\nDemo finished.")


def run_automated_demo():
    """Run automated demo showing various ePTZ operations."""
    print("\n" + "="*60)
    print("Running Automated ePTZ Demo")
    print("="*60 + "\n")
    
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
    
    # Initialize ePTZ controller
    controller = ePTZController(picam2, output_size)
    controller.apply_crop()
    
    try:
        print("Starting with full field of view...")
        print(controller.get_status())
        time.sleep(2)
        
        print("\nZooming in 2x...")
        controller.smooth_zoom_to(2.0, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nZooming in 4x...")
        controller.smooth_zoom_to(4.0, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nPanning to top-left...")
        controller.smooth_pan_to(0.25, 0.25, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nPanning to top-right...")
        controller.smooth_pan_to(0.75, 0.25, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nPanning to bottom-right...")
        controller.smooth_pan_to(0.75, 0.75, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nPanning to bottom-left...")
        controller.smooth_pan_to(0.25, 0.75, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nReturning to center...")
        controller.smooth_pan_to(0.5, 0.5, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nZooming out...")
        controller.smooth_zoom_to(1.0, duration=2.0)
        print(controller.get_status())
        time.sleep(1)
        
        print("\nDemo complete!")
    
    finally:
        picam2.stop()
        picam2.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        # Run automated demo
        run_automated_demo()
    elif HAS_READCHAR:
        # Run interactive demo
        run_interactive_demo()
    else:
        # Run automated demo as fallback
        print("Running automated demo (install 'readchar' for interactive mode)")
        run_automated_demo()

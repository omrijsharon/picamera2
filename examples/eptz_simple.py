#!/usr/bin/python3

"""
Simple ePTZ Example - Basic Pan-Tilt-Zoom

This is a minimal example showing how to use ScalerCrop for electronic PTZ.
It demonstrates:
1. Getting sensor resolution
2. Configuring lower output resolution
3. Calculating crop region
4. Applying zoom
5. Applying pan/tilt

Output: 480p video from 4K sensor with digital zoom and pan
"""

import time
from picamera2_contrib import Picamera2, Preview

# Initialize camera
picam2 = Picamera2()

# Get sensor information
sensor_width, sensor_height = picam2.camera_properties['PixelArraySize']
print(f"Sensor resolution: {sensor_width}x{sensor_height}")

# Configure camera for lower resolution output (e.g., 480p from 4K sensor)
output_width, output_height = 640, 480
config = picam2.create_video_configuration(main={"size": (output_width, output_height)})
picam2.configure(config)

# Start preview
picam2.start_preview(Preview.QTGL)
picam2.start()

# Let camera warm up
time.sleep(2)

print("\nStarting ePTZ demonstration...")


def set_crop(zoom_factor=1.0, pan_x=0.5, pan_y=0.5):
    """
    Set the sensor crop region for ePTZ.
    
    Args:
        zoom_factor: 1.0 = no zoom, 2.0 = 2x zoom, 4.0 = 4x zoom, etc.
        pan_x: Horizontal position (0.0 = left edge, 0.5 = center, 1.0 = right edge)
        pan_y: Vertical position (0.0 = top edge, 0.5 = center, 1.0 = bottom edge)
    """
    # Calculate crop size based on zoom
    crop_width = int(sensor_width / zoom_factor)
    crop_height = int(sensor_height / zoom_factor)
    
    # Maintain output aspect ratio
    output_aspect = output_width / output_height
    crop_aspect = crop_width / crop_height
    
    if crop_aspect > output_aspect:
        # Crop is wider, reduce width
        crop_width = int(crop_height * output_aspect)
    else:
        # Crop is taller, reduce height
        crop_height = int(crop_width / output_aspect)
    
    # Calculate position
    x = int((sensor_width - crop_width) * pan_x)
    y = int((sensor_height - crop_height) * pan_y)
    
    # Ensure even values (hardware requirement)
    x = (x // 2) * 2
    y = (y // 2) * 2
    crop_width = (crop_width // 2) * 2
    crop_height = (crop_height // 2) * 2
    
    # Apply crop
    crop = (x, y, crop_width, crop_height)
    picam2.set_controls({"ScalerCrop": crop})
    
    print(f"Zoom: {zoom_factor}x, Pan: ({pan_x:.1f}, {pan_y:.1f}), "
          f"Crop: ({x}, {y}, {crop_width}, {crop_height})")
    
    return crop


try:
    # Example 1: Full field of view (no zoom)
    print("\n1. Full field of view (1x zoom)")
    set_crop(zoom_factor=1.0, pan_x=0.5, pan_y=0.5)
    time.sleep(3)
    
    # Example 2: 2x digital zoom, centered
    print("\n2. 2x zoom, centered")
    set_crop(zoom_factor=2.0, pan_x=0.5, pan_y=0.5)
    time.sleep(3)
    
    # Example 3: 2x zoom, focus on top-left
    print("\n3. 2x zoom, top-left corner")
    set_crop(zoom_factor=2.0, pan_x=0.25, pan_y=0.25)
    time.sleep(3)
    
    # Example 4: 2x zoom, focus on top-right
    print("\n4. 2x zoom, top-right corner")
    set_crop(zoom_factor=2.0, pan_x=0.75, pan_y=0.25)
    time.sleep(3)
    
    # Example 5: 2x zoom, focus on bottom-right
    print("\n5. 2x zoom, bottom-right corner")
    set_crop(zoom_factor=2.0, pan_x=0.75, pan_y=0.75)
    time.sleep(3)
    
    # Example 6: 4x zoom, centered
    print("\n6. 4x zoom, centered")
    set_crop(zoom_factor=4.0, pan_x=0.5, pan_y=0.5)
    time.sleep(3)
    
    # Example 7: Smooth zoom in
    print("\n7. Smooth zoom from 1x to 3x")
    for zoom in [1.0, 1.5, 2.0, 2.5, 3.0]:
        set_crop(zoom_factor=zoom, pan_x=0.5, pan_y=0.5)
        time.sleep(0.5)
    time.sleep(2)
    
    # Example 8: Pan across from left to right
    print("\n8. Pan from left to right")
    for pan in [0.2, 0.4, 0.5, 0.6, 0.8]:
        set_crop(zoom_factor=2.0, pan_x=pan, pan_y=0.5)
        time.sleep(0.5)
    time.sleep(2)
    
    # Example 9: Reset to full view
    print("\n9. Reset to full field of view")
    set_crop(zoom_factor=1.0, pan_x=0.5, pan_y=0.5)
    time.sleep(3)
    
    print("\nDemo complete!")

finally:
    picam2.stop()
    picam2.close()

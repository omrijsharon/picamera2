#!/usr/bin/python3

"""
FPV rotation test with overlay.
Tests that overlays rotate correctly with the video.
"""

import time
import numpy as np
from libcamera import Transform
from picamera2_contrib import Picamera2, Preview

print("\n" + "="*60)
print("FPV 90° ROTATION TEST WITH OVERLAY")
print("="*60)
print("\nThis tests that overlays rotate correctly with the video.")
print("You should see colored rectangles that stay aligned with the image.\n")

# Create camera
picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)

# Start preview with 90-degree rotation
print("Starting preview with 90° rotation...")
picam2.start_preview(Preview.QT, transform=Transform(transpose=1, vflip=1))
picam2.start()

print("Waiting for camera to warm up...")
time.sleep(1)

# Create a test overlay with colored rectangles
print("Adding overlay...")
overlay = np.zeros((300, 400, 4), dtype=np.uint8)
# Red rectangle (top-right)
overlay[:150, 200:] = (255, 0, 0, 128)
# Green rectangle (bottom-left)
overlay[150:, :200] = (0, 255, 0, 128)
# Blue rectangle (bottom-right)
overlay[150:, 200:] = (0, 0, 255, 128)

picam2.set_overlay(overlay)

print("\n✓ Preview running with 90° rotation and overlay")
print("✓ You should see 3 colored rectangles")
print("✓ They should rotate with the video")
print("\nPress Ctrl+C to exit...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nStopping...")

picam2.stop()
picam2.close()

print("\n" + "="*60)
print("Test complete!")
print("="*60)
print("\nIf the overlay rotated with the video, everything is working!\n")

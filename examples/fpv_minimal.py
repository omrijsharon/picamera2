#!/usr/bin/python3

"""
Minimal FPV overlay example - Clean and simple.

This is the cleanest way to add an FPV HUD with the OverlayHelper.
Perfect starting point for your FPV drone project.
"""

import time
from libcamera import Transform
from picamera2_contrib import Picamera2, Preview
from picamera2_contrib.overlay_helper import FPVOverlay

# Setup camera
picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)

# Get display size for overlay
stream = picam2.stream_map[config['display']]
width = stream.configuration.size.width
height = stream.configuration.size.height

# Create FPV overlay
hud = FPVOverlay(width, height)

# Add static HUD elements (one-time setup)
hud.add_crosshair(size=25, color=(255, 0, 0, 180), thickness=2)
hud.update_flight_mode("ACRO")

# Start preview with 90° rotation
picam2.start_preview(Preview.QT, transform=Transform(transpose=1, vflip=1))
picam2.start()
picam2.set_overlay(hud.get_array())

print("FPV Camera Ready!")
print("Press Ctrl+C to exit...\n")

# Main loop - update telemetry
try:
    while True:
        # Read telemetry (replace with your actual sensors)
        voltage = 11.8  # Read from your battery monitor
        signal = 85     # Read from your radio receiver
        
        # Update HUD (takes <0.05ms)
        hud.update_battery(voltage, cell_count=3)
        hud.update_signal(signal)
        
        # Push update to camera
        picam2.set_overlay(hud.get_array())
        
        time.sleep(0.1)  # 10 Hz update rate
        
except KeyboardInterrupt:
    print("\nShutting down...")

picam2.stop()
picam2.close()
print("Done!")

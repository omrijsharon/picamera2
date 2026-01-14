#!/usr/bin/python3

"""
Demo of the efficient OverlayHelper for FPV applications.

This shows how to create and update overlays with minimal latency.
Perfect for real-time FPV drone HUD with dynamic telemetry data.
"""

import time
import random
from libcamera import Transform
from picamera2 import Picamera2, Preview
from picamera2.overlay_helper import FPVOverlay

print("\n" + "="*60)
print("EFFICIENT OVERLAY HELPER TEST")
print("="*60)
print("\nThis demonstrates the high-performance overlay system.")
print("You'll see a dynamic FPV HUD with minimal latency.\n")

# Create camera
picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)

# Get display stream size for overlay
display_stream = picam2.stream_map[config['display']]
width = display_stream.configuration.size.width
height = display_stream.configuration.size.height

print(f"Display resolution: {width}x{height}")

# Start preview with 90-degree rotation
print("Starting preview with 90° rotation...")
picam2.start_preview(Preview.QT, transform=Transform(transpose=1, vflip=1))
picam2.start()

print("Waiting for camera to warm up...")
time.sleep(1)

# Create FPV overlay helper
print("Creating FPV overlay...")
overlay = FPVOverlay(width, height)

# Add static elements (one-time setup)
print("Adding static HUD elements...")
overlay.add_crosshair(size=30, color=(255, 0, 0, 200), thickness=2)

# Add static corner markers
overlay.add_rectangle("corner_tl", 10, 10, 10, 10, (0, 255, 0, 150))
overlay.add_rectangle("corner_tr", width - 20, 10, 10, 10, (0, 255, 0, 150))
overlay.add_rectangle("corner_bl", 10, height - 20, 10, 10, (0, 255, 0, 150))
overlay.add_rectangle("corner_br", width - 20, height - 20, 10, 10, (0, 255, 0, 150))

# Add flight mode
overlay.update_flight_mode("ACRO")

# Set the initial overlay
picam2.set_overlay(overlay.get_array())

print("\n✓ Overlay initialized")
print("✓ Starting dynamic updates (battery, signal, time)...")
print("\nYou should see:")
print("  - Red crosshair in center")
print("  - Green corner markers")
print("  - Flight mode in top-right")
print("  - Battery voltage (simulated, changes color)")
print("  - Signal strength (simulated, changes color)")
print("  - Timer")
print("\nPress Ctrl+C to exit...\n")

# Simulate dynamic telemetry updates
start_time = time.time()
frame_count = 0
update_times = []

try:
    while True:
        # Simulate telemetry data
        voltage = 12.6 - (random.random() * 2)  # Simulate battery drain
        signal = random.randint(40, 100)  # Simulate signal fluctuation
        elapsed = time.time() - start_time
        
        # Measure update time
        update_start = time.perf_counter()
        
        # Update dynamic elements (this is the critical path)
        overlay.update_battery(voltage, cell_count=3, x=10, y=30)
        overlay.update_signal(signal, x=10, y=60)
        
        # Add timer
        overlay.update_text("timer", 10, 90, f"TIME: {elapsed:.1f}s",
                          (255, 255, 255, 255), font_scale=0.6, thickness=2)
        
        # Update the overlay (only this part touches picamera2)
        picam2.set_overlay(overlay.get_array())
        
        update_end = time.perf_counter()
        update_time_ms = (update_end - update_start) * 1000
        update_times.append(update_time_ms)
        
        frame_count += 1
        
        # Print stats every 5 seconds
        if frame_count % 50 == 0:
            avg_time = sum(update_times[-50:]) / len(update_times[-50:])
            stats = overlay.get_stats()
            print(f"Frame {frame_count}: Avg update time: {avg_time:.3f}ms | "
                  f"Elements: {stats['elements']} | "
                  f"Voltage: {voltage:.1f}V | Signal: {signal}%")
        
        time.sleep(0.1)  # 10 Hz update rate
        
except KeyboardInterrupt:
    print("\n\nStopping...")

# Print final statistics
if update_times:
    avg_time = sum(update_times) / len(update_times)
    min_time = min(update_times)
    max_time = max(update_times)
    
    print("\n" + "="*60)
    print("PERFORMANCE STATISTICS")
    print("="*60)
    print(f"Total frames: {frame_count}")
    print(f"Average update time: {avg_time:.3f}ms")
    print(f"Min update time: {min_time:.3f}ms")
    print(f"Max update time: {max_time:.3f}ms")
    
    stats = overlay.get_stats()
    print(f"\nOverlay stats:")
    print(f"  Elements: {stats['elements']}")
    print(f"  Total updates: {stats['updates']}")
    print(f"  Memory: {stats['memory_mb']:.2f} MB")
    print("\n✓ Overlay helper is highly efficient!")
    print(f"✓ Update latency: ~{avg_time:.2f}ms (target: <0.2ms)")

picam2.stop()
picam2.close()

print("\n" + "="*60)
print("Test complete!")
print("="*60 + "\n")

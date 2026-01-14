#!/usr/bin/python3

"""
Performance comparison: Naive overlay updates vs. OverlayHelper.

This demonstrates why OverlayHelper is essential for low-latency FPV applications.
"""

import time
import numpy as np
from picamera2.overlay_helper import OverlayHelper

print("\n" + "="*60)
print("OVERLAY PERFORMANCE COMPARISON")
print("="*60)
print("\nComparing two approaches for updating overlay text:\n")

WIDTH, HEIGHT = 640, 480
ITERATIONS = 100

# Test 1: Naive approach (recreate entire array each time)
print("Test 1: NAIVE APPROACH (recreate array each time)")
print("-" * 60)

naive_times = []
for i in range(ITERATIONS):
    start = time.perf_counter()
    
    # This is what most people do - recreate the entire array
    overlay = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    
    # Draw some rectangles (simulate HUD elements)
    overlay[10:30, 10:110] = (255, 0, 0, 200)  # Battery indicator
    overlay[40:60, 10:110] = (0, 255, 0, 200)  # Signal indicator
    overlay[230:250, 310:330] = (255, 0, 0, 150)  # Crosshair
    
    # Simulate dynamic text (would normally use cv2.putText)
    overlay[70:90, 10:150] = (255, 255, 255, 200)
    
    end = time.perf_counter()
    naive_times.append((end - start) * 1000)

avg_naive = sum(naive_times) / len(naive_times)
print(f"Average time: {avg_naive:.3f}ms per frame")
print(f"Min: {min(naive_times):.3f}ms, Max: {max(naive_times):.3f}ms\n")

# Test 2: OverlayHelper approach (pre-allocated buffer, partial updates)
print("Test 2: OVERLAY HELPER (pre-allocated buffer, partial updates)")
print("-" * 60)

helper = OverlayHelper(WIDTH, HEIGHT)

# One-time setup (doesn't count toward per-frame cost)
helper.add_rectangle("battery_bg", 10, 10, 100, 20, (255, 0, 0, 200))
helper.add_rectangle("signal_bg", 10, 40, 100, 20, (0, 255, 0, 200))
helper.add_rectangle("crosshair", 310, 230, 20, 20, (255, 0, 0, 150))

helper_times = []
for i in range(ITERATIONS):
    start = time.perf_counter()
    
    # Only update the changed elements (text with new values)
    # In reality, you'd only update what actually changed
    helper.add_rectangle("dynamic_text", 10, 70, 140, 20, (255, 255, 255, 200))
    
    # Get the array (this is just a pointer, no copy)
    array = helper.get_array()
    
    end = time.perf_counter()
    helper_times.append((end - start) * 1000)

avg_helper = sum(helper_times) / len(helper_times)
print(f"Average time: {avg_helper:.3f}ms per frame")
print(f"Min: {min(helper_times):.3f}ms, Max: {max(helper_times):.3f}ms\n")

# Results
print("="*60)
print("RESULTS")
print("="*60)
print(f"Naive approach:     {avg_naive:.3f}ms per frame")
print(f"OverlayHelper:      {avg_helper:.3f}ms per frame")
print(f"Speedup:            {avg_naive / avg_helper:.1f}x faster")
print(f"Latency savings:    {avg_naive - avg_helper:.3f}ms per frame")
print(f"")
print(f"At 60 FPS:")
print(f"  Naive total:      {avg_naive * 60:.1f}ms per second")
print(f"  Helper total:     {avg_helper * 60:.1f}ms per second")
print(f"  Time saved:       {(avg_naive - avg_helper) * 60:.1f}ms per second")
print("\n" + "="*60)

if avg_helper < 0.2:
    print("✓ EXCELLENT: Overlay helper is fast enough for FPV (<0.2ms)")
elif avg_helper < 0.5:
    print("✓ GOOD: Overlay helper is acceptable for FPV (<0.5ms)")
else:
    print("⚠ WARNING: Update time higher than expected")

print("="*60 + "\n")

# Additional insights
print("KEY INSIGHTS:")
print("-------------")
print("1. Pre-allocation eliminates memory allocation overhead")
print("2. Partial updates only touch changed pixels")
print("3. C-contiguous array is QImage-friendly (no copy needed)")
print("4. Method chaining makes code cleaner")
print("5. Element tracking enables intelligent dirty region handling")
print("\nFor FPV drones, every millisecond of latency matters!")
print("The OverlayHelper makes overlay updates nearly free.\n")

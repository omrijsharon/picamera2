#!/usr/bin/env python3
"""
Detailed sensor mode analysis for IMX708 camera.
Determines which modes are binned vs cropped, and analyzes ePTZ capabilities.
"""
from picamera2_contrib import Picamera2
import sys

def analyze_sensor_modes():
    """Analyze all available sensor modes and their characteristics."""
    
    print("=" * 80)
    print("IMX708 SENSOR MODE ANALYSIS")
    print("=" * 80)
    
    picam2 = Picamera2()
    
    # Get sensor information
    sensor_size = picam2.camera_properties.get('PixelArraySize')
    print(f"\nFull Sensor Resolution: {sensor_size[0]}x{sensor_size[1]}")
    print(f"Total Pixels: {sensor_size[0] * sensor_size[1] / 1_000_000:.1f} MP")
    
    # Get all available sensor modes
    modes = picam2.sensor_modes
    print(f"\nFound {len(modes)} sensor modes:")
    print("-" * 80)
    
    for idx, mode in enumerate(modes):
        size = mode['size']
        fps = mode['fps']
        fmt = mode.get('format', 'Unknown')
        bit_depth = mode.get('bit_depth', 'Unknown')
        
        # Calculate pixel ratio compared to full sensor
        mode_pixels = size[0] * size[1]
        full_pixels = sensor_size[0] * sensor_size[1]
        pixel_ratio = mode_pixels / full_pixels
        
        # Determine if binned or cropped
        width_ratio = sensor_size[0] / size[0]
        height_ratio = sensor_size[1] / size[1]
        
        print(f"\n[MODE {idx}]")
        print(f"  Resolution: {size[0]}x{size[1]} ({mode_pixels / 1_000_000:.1f} MP)")
        print(f"  Max FPS: {fps:.2f}")
        print(f"  Format: {fmt}, Bit Depth: {bit_depth}")
        print(f"  Pixel Coverage: {pixel_ratio * 100:.1f}% of full sensor")
        print(f"  Width Ratio: {width_ratio:.2f}x, Height Ratio: {height_ratio:.2f}x")
        
        # Classify mode type
        if abs(width_ratio - height_ratio) < 0.1:  # Ratios are similar
            if width_ratio >= 1.9 and width_ratio <= 2.1:
                mode_type = "2x2 BINNED (hardware averages 4 pixels into 1)"
            elif width_ratio >= 3.9 and width_ratio <= 4.1:
                mode_type = "4x4 BINNED (hardware averages 16 pixels into 1)"
            elif width_ratio >= 0.9 and width_ratio <= 1.1:
                mode_type = "FULL SENSOR (no binning)"
            else:
                mode_type = f"{width_ratio:.1f}x BINNED/SUBSAMPLED"
        else:
            mode_type = "CENTER CROP (sensor reads smaller area)"
        
        print(f"  Mode Type: {mode_type}")
        
        # Calculate frame latency
        frame_time_ms = 1000 / fps
        print(f"  Frame Latency: {frame_time_ms:.1f}ms between frames")
        
        # FPV suitability
        if fps >= 100:
            fpv_rating = "✅ EXCELLENT for FPV (very low latency)"
        elif fps >= 50:
            fpv_rating = "✅ GOOD for FPV (acceptable latency)"
        elif fps >= 30:
            fpv_rating = "⚠️ MARGINAL for FPV (noticeable lag)"
        else:
            fpv_rating = "❌ POOR for FPV (too much lag)"
        print(f"  FPV Rating: {fpv_rating}")
        
        # ePTZ zoom range calculation
        # Maximum zoom is limited by output resolution
        # Assuming 640x480 output
        output_w, output_h = 640, 480
        max_zoom_w = size[0] / output_w
        max_zoom_h = size[1] / output_h
        max_zoom = min(max_zoom_w, max_zoom_h)
        print(f"  ePTZ Max Zoom (for 640x480 output): {max_zoom:.2f}x")
        
        # Pan range
        pan_range_x = size[0] - output_w
        pan_range_y = size[1] - output_h
        print(f"  ePTZ Pan Range: {pan_range_x}px horizontal, {pan_range_y}px vertical")
    
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    # Find best mode for different use cases
    modes_by_fps = sorted(modes, key=lambda m: m['fps'], reverse=True)
    modes_by_area = sorted(modes, key=lambda m: m['size'][0] * m['size'][1], reverse=True)
    
    print("\n[RECOMMENDATIONS]")
    print(f"\n1. Best for FPV (highest FPS):")
    best_fpv = modes_by_fps[0]
    print(f"   Mode {modes.index(best_fpv)}: {best_fpv['size'][0]}x{best_fpv['size'][1]} @ {best_fpv['fps']:.1f} FPS")
    print(f"   Trade-off: Only {best_fpv['size'][0] * best_fpv['size'][1] / full_pixels * 100:.1f}% of sensor area")
    
    print(f"\n2. Best for Wide FOV (largest area):")
    best_fov = modes_by_area[0]
    print(f"   Mode {modes.index(best_fov)}: {best_fov['size'][0]}x{best_fov['size'][1]} @ {best_fov['fps']:.1f} FPS")
    print(f"   Trade-off: Only {best_fov['fps']:.1f} FPS ({1000/best_fov['fps']:.1f}ms latency)")
    
    print(f"\n3. Balanced (middle ground):")
    if len(modes) >= 2:
        balanced = modes_by_fps[1] if len(modes_by_fps) > 1 else modes_by_fps[0]
        print(f"   Mode {modes.index(balanced)}: {balanced['size'][0]}x{balanced['size'][1]} @ {balanced['fps']:.1f} FPS")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print("""
1. Sensor Mode vs ScalerCrop:
   - Sensor MODE determines framerate (hardware binning/cropping)
   - ScalerCrop (ePTZ) is applied AFTER sensor readout
   - ScalerCrop does NOT affect framerate

2. For FPV Drones:
   - Use highest FPS mode (accept narrower FOV)
   - Low latency > Wide FOV for flying
   - Disable AE/AWB for consistent frame timing

3. For Wide FOV:
   - Use full sensor mode (accept lower FPS)
   - More ePTZ zoom range available
   - Better for stationary/slow applications

4. ISP Scaling:
   - Hardware accelerated, "free" performance
   - Can output any resolution (480p, 720p, etc.)
   - Scaling does NOT affect framerate
""")

if __name__ == "__main__":
    try:
        analyze_sensor_modes()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

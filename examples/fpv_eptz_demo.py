#!/usr/bin/python3

"""
FPV Drone Camera with ePTZ

This example demonstrates a low-latency FPV camera configuration with ePTZ capability.
Optimized for:
- High framerate (60-120 FPS) for low latency
- 480p output (sufficient for FPV transmission)
- Minimal buffering
- Optional digital pan/tilt/zoom within the sensor area

For FPV, framerate is MORE important than wide field of view.
"""

import time
from picamera2 import Picamera2

def calculate_crop(sensor_width, sensor_height, output_width, output_height, 
                   zoom_factor=1.0, pan_x=0.5, pan_y=0.5):
    """
    Calculate ScalerCrop values for ePTZ.
    
    Args:
        sensor_width: Sensor width in pixels
        sensor_height: Sensor height in pixels
        output_width: Output width
        output_height: Output height
        zoom_factor: Zoom level (1.0 = no zoom)
        pan_x: Horizontal position (0.0-1.0, 0.5 = center)
        pan_y: Vertical position (0.0-1.0, 0.5 = center)
    
    Returns:
        Tuple of (x, y, width, height) for ScalerCrop
    """
    output_aspect = output_width / output_height
    sensor_aspect = sensor_width / sensor_height
    
    crop_width = int(sensor_width / zoom_factor)
    crop_height = int(sensor_height / zoom_factor)
    
    # Maintain aspect ratio
    if output_aspect > sensor_aspect:
        crop_height = int(crop_width / output_aspect)
    else:
        crop_width = int(crop_height * output_aspect)
    
    # Calculate position
    max_x = sensor_width - crop_width
    max_y = sensor_height - crop_height
    
    x = int(max_x * pan_x)
    y = int(max_y * pan_y)
    
    # Ensure even values
    x = (x // 2) * 2
    y = (y // 2) * 2
    crop_width = (crop_width // 2) * 2
    crop_height = (crop_height // 2) * 2
    
    return (x, y, crop_width, crop_height)


def main():
    picam2 = Picamera2()
    
    print("=" * 60)
    print("FPV DRONE CAMERA - LOW LATENCY CONFIGURATION")
    print("=" * 60)
    
    # Find fastest sensor mode
    print("\nAvailable sensor modes:")
    available_modes = picam2.sensor_modes
    for mode in available_modes:
        latency_ms = 1000.0 / mode['fps']
        print(f"  {mode['size']} @ {mode['fps']:.1f} FPS (latency: {latency_ms:.1f}ms/frame)")
    
    # Sort by FPS and select fastest
    available_modes.sort(key=lambda x: x["fps"], reverse=True)
    fpv_mode = available_modes[0]
    
    print(f"\n✓ Selected FPV mode: {fpv_mode['size']} @ {fpv_mode['fps']:.1f} FPS")
    print(f"  Frame latency: {1000.0/fpv_mode['fps']:.1f}ms")
    
    # Configure for low-latency FPV
    output_resolution = (640, 480)
    config = picam2.create_video_configuration(
        main={"size": output_resolution, "format": "XRGB8888"},
        raw={"size": fpv_mode['size'], "format": fpv_mode['format'].format},
        buffer_count=2,  # Minimal buffering for low latency
    )
    picam2.configure(config)
    
    print(f"✓ Output: {output_resolution[0]}x{output_resolution[1]} (480p)")
    print(f"✓ Buffer count: 2 (low latency)")
    
    # Fixed exposure settings for consistent frame timing
    exposure_time = 5000  # 5ms exposure
    analogue_gain = 2.0
    
    picam2.set_controls({
        "FrameRate": fpv_mode['fps'],
        "AeEnable": False,      # Disable auto-exposure
        "AwbEnable": False,     # Disable auto white balance
        "ExposureTime": exposure_time,
        "AnalogueGain": analogue_gain,
    })
    
    print(f"✓ Fixed exposure: {exposure_time}µs, Gain: {analogue_gain}x")
    print("  (Disabled AE/AWB for consistent latency)")
    
    picam2.start()
    print("\n✓ Camera started!")
    
    # Get sensor dimensions for ePTZ
    sensor_w, sensor_h = fpv_mode['size']
    
    print("\n" + "=" * 60)
    print("EPTZ DEMONSTRATION")
    print("=" * 60)
    print("\nNote: ePTZ does NOT affect framerate - it's applied after sensor readout")
    
    # Demo 1: Default view (no zoom)
    print("\n[1/4] Default view (no zoom)")
    crop = calculate_crop(sensor_w, sensor_h, *output_resolution, zoom_factor=1.0)
    picam2.set_controls({"ScalerCrop": crop})
    print(f"      Crop: {crop}")
    time.sleep(2)
    
    # Demo 2: Slight zoom for better framing
    print("\n[2/4] Slight zoom (1.2x) - useful for removing edge distortion")
    crop = calculate_crop(sensor_w, sensor_h, *output_resolution, zoom_factor=1.2)
    picam2.set_controls({"ScalerCrop": crop})
    print(f"      Crop: {crop}")
    time.sleep(2)
    
    # Demo 3: Pan up (look at sky/horizon)
    print("\n[3/4] Pan up (tilt_up) - useful for climbing")
    crop = calculate_crop(sensor_w, sensor_h, *output_resolution, 
                         zoom_factor=1.0, pan_x=0.5, pan_y=0.3)  # pan_y < 0.5 = up
    picam2.set_controls({"ScalerCrop": crop})
    print(f"      Crop: {crop}")
    time.sleep(2)
    
    # Demo 4: Pan down (look at ground)
    print("\n[4/4] Pan down (tilt_down) - useful for landing")
    crop = calculate_crop(sensor_w, sensor_h, *output_resolution, 
                         zoom_factor=1.0, pan_x=0.5, pan_y=0.7)  # pan_y > 0.5 = down
    picam2.set_controls({"ScalerCrop": crop})
    print(f"      Crop: {crop}")
    time.sleep(2)
    
    # Return to default
    print("\n[Reset] Back to default view")
    crop = calculate_crop(sensor_w, sensor_h, *output_resolution, zoom_factor=1.0)
    picam2.set_controls({"ScalerCrop": crop})
    
    print("\n" + "=" * 60)
    print("FPV USE CASES FOR EPTZ")
    print("=" * 60)
    print("""
1. FLIGHT MODE ADJUSTMENT:
   - Cruising: Default view (1.0x zoom, centered)
   - Racing: Slight zoom (1.2x) to reduce wide-angle distortion
   - Acro tricks: Pan up/down based on orientation

2. TAKEOFF/LANDING:
   - Takeoff: Pan down to see landing pad
   - Landing: Pan down to see ground clearly
   - Return to center for normal flight

3. HORIZON LOCK:
   - Use IMU data to counter drone tilt
   - Keep horizon level in FPV feed using pan_y
   - Reduces pilot disorientation

4. DYNAMIC ZOOM:
   - Zoom in when flying slow (precision)
   - Zoom out when flying fast (situational awareness)
   - Control via flight controller stick/switch

INTEGRATION TIPS:
- Connect to MAVLink/Betaflight for flight mode
- Use RC channel to control zoom/pan
- Map to OSD menu for in-flight adjustment
- Consider gyro stabilization with ePTZ
""")
    
    print("\nPress Ctrl+C to exit...")
    
    try:
        # Main loop - this is where you'd stream to FPV transmitter
        frame_count = 0
        start_time = time.time()
        
        while True:
            # Capture frame (replace with your FPV streaming code)
            array = picam2.capture_array("main")
            frame_count += 1
            
            # Show stats every 100 frames
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                actual_fps = frame_count / elapsed
                print(f"Streaming: {actual_fps:.1f} FPS (actual), "
                      f"{frame_count} frames in {elapsed:.1f}s")
                
                # Reset counters
                frame_count = 0
                start_time = time.time()
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    
    finally:
        picam2.stop()
        print("✓ Camera stopped")
        print("\nFor FPV production:")
        print("  - Add video encoding (H264/MJPEG)")
        print("  - Stream via UDP/RTP to FPV transmitter")
        print("  - Integrate with flight controller for dynamic ePTZ")
        print("  - See fpv_minimal.py for OSD overlay example")


if __name__ == "__main__":
    main()

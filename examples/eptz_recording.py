#!/usr/bin/python3

"""
ePTZ Video Recording Example

This example shows how to use ePTZ (electronic pan-tilt-zoom) while recording video.
It demonstrates:
- Recording 480p video from a high-resolution sensor
- Applying zoom during recording
- Creating a cinematic effect by slowly zooming and panning

The advantage of using ePTZ during recording is that you can:
- Record at lower bitrate/file size while maintaining source quality
- Add dynamic camera movements without a physical gimbal
- Extract specific regions of interest from a wide scene
- Create multiple videos from one recording by changing ePTZ settings

Output: MP4 file with ePTZ effects applied
"""

import time
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput


def calculate_crop(sensor_size, output_size, zoom=1.0, pan_x=0.5, pan_y=0.5):
    """
    Calculate ScalerCrop values for ePTZ.
    
    Args:
        sensor_size: (width, height) of sensor in pixels
        output_size: (width, height) of output video
        zoom: Zoom factor (1.0 = no zoom, 2.0 = 2x, etc.)
        pan_x: Horizontal position (0.0 = left, 0.5 = center, 1.0 = right)
        pan_y: Vertical position (0.0 = top, 0.5 = center, 1.0 = bottom)
    
    Returns:
        Tuple (x, y, width, height) for ScalerCrop control
    """
    sensor_width, sensor_height = sensor_size
    output_width, output_height = output_size
    output_aspect = output_width / output_height
    
    # Calculate crop size
    crop_width = int(sensor_width / zoom)
    crop_height = int(sensor_height / zoom)
    
    # Maintain aspect ratio
    if crop_width / crop_height > output_aspect:
        crop_width = int(crop_height * output_aspect)
    else:
        crop_height = int(crop_width / output_aspect)
    
    # Calculate position
    x = int((sensor_width - crop_width) * pan_x)
    y = int((sensor_height - crop_height) * pan_y)
    
    # Ensure even values (hardware requirement)
    x = (x // 2) * 2
    y = (y // 2) * 2
    crop_width = (crop_width // 2) * 2
    crop_height = (crop_height // 2) * 2
    
    # Clamp to valid range
    x = max(0, min(x, sensor_width - crop_width))
    y = max(0, min(y, sensor_height - crop_height))
    
    return (x, y, crop_width, crop_height)


def smooth_transition(picam2, sensor_size, output_size, 
                     start_zoom, end_zoom, 
                     start_pan_x, end_pan_x,
                     start_pan_y, end_pan_y,
                     duration, steps=60):
    """
    Smoothly transition ePTZ from one state to another.
    
    Args:
        picam2: Picamera2 instance
        sensor_size: Sensor dimensions
        output_size: Output dimensions
        start_zoom, end_zoom: Start and end zoom levels
        start_pan_x, end_pan_x: Start and end horizontal pan
        start_pan_y, end_pan_y: Start and end vertical pan
        duration: Duration in seconds
        steps: Number of steps for smooth transition
    """
    for i in range(steps + 1):
        progress = i / steps
        
        # Interpolate values
        zoom = start_zoom + (end_zoom - start_zoom) * progress
        pan_x = start_pan_x + (end_pan_x - start_pan_x) * progress
        pan_y = start_pan_y + (end_pan_y - start_pan_y) * progress
        
        # Apply crop
        crop = calculate_crop(sensor_size, output_size, zoom, pan_x, pan_y)
        picam2.set_controls({"ScalerCrop": crop})
        
        # Wait
        time.sleep(duration / steps)


def record_with_eptz_effects(output_file="eptz_video.mp4", duration=30):
    """
    Record a video with various ePTZ effects.
    
    Args:
        output_file: Output video filename
        duration: Total recording duration in seconds
    """
    print("\n" + "="*60)
    print(f"Recording Video with ePTZ Effects")
    print("="*60)
    print(f"\nOutput file: {output_file}")
    print(f"Duration: {duration} seconds")
    print(f"Resolution: 640x480 (480p)")
    print("\nEffects sequence:")
    print("  1. Start wide (full field of view)")
    print("  2. Slow zoom in to 3x")
    print("  3. Pan from left to right")
    print("  4. Zoom out while panning back to center")
    print("\nStarting in 2 seconds...\n")
    
    # Initialize camera
    picam2 = Picamera2()
    
    # Get sensor info
    sensor_size = picam2.camera_properties['PixelArraySize']
    print(f"Sensor resolution: {sensor_size[0]}x{sensor_size[1]}")
    
    # Configure for 480p output
    output_size = (640, 480)
    config = picam2.create_video_configuration(
        main={"size": output_size}
    )
    picam2.configure(config)
    
    # Setup encoder
    encoder = H264Encoder(bitrate=2000000)  # 2 Mbps
    output = FfmpegOutput(output_file)
    
    # Start recording
    picam2.start_recording(encoder, output)
    
    # Wait a moment
    time.sleep(2)
    
    try:
        # Calculate timing for each segment
        segment_time = duration / 4
        
        # Segment 1: Start wide
        print(f"[0-{segment_time:.0f}s] Starting with full field of view")
        crop = calculate_crop(sensor_size, output_size, zoom=1.0, pan_x=0.5, pan_y=0.5)
        picam2.set_controls({"ScalerCrop": crop})
        time.sleep(segment_time)
        
        # Segment 2: Slow zoom in
        print(f"[{segment_time:.0f}-{segment_time*2:.0f}s] Zooming in to 3x")
        smooth_transition(
            picam2, sensor_size, output_size,
            start_zoom=1.0, end_zoom=3.0,
            start_pan_x=0.5, end_pan_x=0.5,
            start_pan_y=0.5, end_pan_y=0.5,
            duration=segment_time
        )
        
        # Segment 3: Pan from left to right while zoomed
        print(f"[{segment_time*2:.0f}-{segment_time*3:.0f}s] Panning left to right")
        smooth_transition(
            picam2, sensor_size, output_size,
            start_zoom=3.0, end_zoom=3.0,
            start_pan_x=0.3, end_pan_x=0.7,
            start_pan_y=0.5, end_pan_y=0.5,
            duration=segment_time
        )
        
        # Segment 4: Zoom out while returning to center
        print(f"[{segment_time*3:.0f}-{duration:.0f}s] Zooming out and centering")
        smooth_transition(
            picam2, sensor_size, output_size,
            start_zoom=3.0, end_zoom=1.0,
            start_pan_x=0.7, end_pan_x=0.5,
            start_pan_y=0.5, end_pan_y=0.5,
            duration=segment_time
        )
        
        print(f"\nRecording complete!")
        
    except KeyboardInterrupt:
        print("\n\nRecording interrupted by user")
    
    finally:
        # Stop recording
        picam2.stop_recording()
        picam2.close()
        
        print(f"\nVideo saved to: {output_file}")
        print("You can play it with: vlc " + output_file)


def record_security_patrol(output_file="security_patrol.mp4", duration=20):
    """
    Simulate a security camera patrol pattern.
    
    This creates a video that pans through different areas as if a security
    camera is monitoring different zones.
    """
    print("\n" + "="*60)
    print(f"Recording Security Patrol Pattern")
    print("="*60)
    print(f"\nOutput file: {output_file}")
    print(f"Duration: {duration} seconds")
    print("\nPatrol pattern: Top-left → Top-right → Bottom-right → Bottom-left → Center")
    print("\nStarting in 2 seconds...\n")
    
    # Initialize camera
    picam2 = Picamera2()
    sensor_size = picam2.camera_properties['PixelArraySize']
    output_size = (640, 480)
    
    config = picam2.create_video_configuration(main={"size": output_size})
    picam2.configure(config)
    
    encoder = H264Encoder(bitrate=2000000)
    output = FfmpegOutput(output_file)
    
    picam2.start_recording(encoder, output)
    time.sleep(2)
    
    try:
        # Define patrol points (pan_x, pan_y, zoom, duration)
        patrol_points = [
            (0.25, 0.25, 2.0, duration/5),  # Top-left
            (0.75, 0.25, 2.0, duration/5),  # Top-right
            (0.75, 0.75, 2.0, duration/5),  # Bottom-right
            (0.25, 0.75, 2.0, duration/5),  # Bottom-left
            (0.5,  0.5,  1.5, duration/5),  # Center, slightly zoomed
        ]
        
        for i, (pan_x, pan_y, zoom, seg_duration) in enumerate(patrol_points):
            print(f"Patrol point {i+1}/5: Pan({pan_x:.2f}, {pan_y:.2f}), Zoom {zoom}x")
            
            if i == 0:
                # First point - jump to it
                crop = calculate_crop(sensor_size, output_size, zoom, pan_x, pan_y)
                picam2.set_controls({"ScalerCrop": crop})
                time.sleep(seg_duration)
            else:
                # Subsequent points - smooth transition
                prev_pan_x, prev_pan_y, prev_zoom, _ = patrol_points[i-1]
                smooth_transition(
                    picam2, sensor_size, output_size,
                    start_zoom=prev_zoom, end_zoom=zoom,
                    start_pan_x=prev_pan_x, end_pan_x=pan_x,
                    start_pan_y=prev_pan_y, end_pan_y=pan_y,
                    duration=seg_duration
                )
        
        print("\nPatrol complete!")
        
    except KeyboardInterrupt:
        print("\n\nRecording interrupted")
    
    finally:
        picam2.stop_recording()
        picam2.close()
        print(f"\nVideo saved to: {output_file}")


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "security":
            # Record security patrol pattern
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            output = sys.argv[3] if len(sys.argv) > 3 else "security_patrol.mp4"
            record_security_patrol(output, duration)
        elif sys.argv[1] == "cinematic":
            # Record with cinematic effects
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            output = sys.argv[3] if len(sys.argv) > 3 else "cinematic.mp4"
            record_with_eptz_effects(output, duration)
        else:
            print("Usage:")
            print("  python eptz_recording.py cinematic [duration] [output.mp4]")
            print("  python eptz_recording.py security [duration] [output.mp4]")
            sys.exit(1)
    else:
        # Default: cinematic recording
        record_with_eptz_effects("eptz_video.mp4", duration=30)

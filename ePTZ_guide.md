# Electronic Pan-Tilt-Zoom (ePTZ) Guide for Picamera2

## Quick Answer for FPV Drones

**For low-latency FPV, you need HIGH framerate (60-120 FPS), not full sensor resolution.**

### Recommended FPV Configuration:

```python
# FPV Priority: High FPS > Wide FOV
# Use binned sensor mode for maximum framerate

# Find fastest sensor mode
available_modes = picam2.sensor_modes
available_modes.sort(key=lambda x: x["fps"], reverse=True)
fast_mode = available_modes[0]

config = picam2.create_video_configuration(
    main={"size": (640, 480)},  # 480p is plenty for FPV
    raw={"size": fast_mode['size'], "format": fast_mode['format'].format},
    controls={"FrameRate": fast_mode['fps']}
)
# Result: ~60-120 FPS with reduced FOV (binned sensor mode)
```

**Why NOT use full sensor for FPV:**
- ❌ Full sensor: 18 FPS = 55ms latency between frames (unusable for FPV)
- ✅ Binned sensor: 60-120 FPS = 8-16ms latency (good for FPV)
- The slightly narrower FOV from binning is acceptable for the massive latency reduction

## Overview

Electronic Pan-Tilt-Zoom (ePTZ) is a technique where you digitally crop and scale a region of the camera sensor to simulate pan, tilt, and zoom operations without physically moving the camera. This is particularly useful when you have a high-resolution sensor (e.g., 4K or higher) but want to output a lower resolution video (e.g., 480p).

This guide explains how to implement ePTZ using the picamera2 library through the `ScalerCrop` control.

## How ePTZ Works in Picamera2

### CRITICAL: Framerate vs Sensor Mode vs ScalerCrop

**There are TWO different concepts that affect framerate:**

1. **Sensor Mode (Hardware)**: The physical sensor configuration (binning/subsampling)
   - Determines what the sensor physically reads out
   - **This sets the maximum framerate**
   - Examples: Full 12MP mode (~18 FPS), 2x2 binned 3MP mode (~40 FPS)

2. **ScalerCrop (Software/ePTZ)**: Digital crop applied AFTER sensor readout
   - **Does NOT change framerate** - the sensor still reads the same amount of data
   - Only affects which part of the sensor data is used
   - This is what ePTZ uses for pan/tilt/zoom

**IMPORTANT**: `ScalerCrop` (ePTZ) does **NOT** make the sensor read faster. You still get the framerate of the underlying sensor mode.

### The ScalerCrop Control

The key to implementing ePTZ in picamera2 is the `ScalerCrop` control, which allows you to:
- Select a rectangular region of the sensor to read from
- The selected region is then scaled to your output resolution

The `ScalerCrop` control is a tuple of 4 values: `(x, y, width, height)`
- `x`: Left offset from sensor origin (in sensor pixels)
- `y`: Top offset from sensor origin (in sensor pixels)  
- `width`: Width of the crop region (in sensor pixels)
- `height`: Height of the crop region (in sensor pixels)

### The Signal Path

Here's how the image flows through the camera pipeline:

```
┌─────────────┐
│   Sensor    │  Full resolution (e.g., 4056x3040 for IMX708)
│  (4K/12MP)  │
└──────┬──────┘
       │
       ├─────────────────────────────────┐
       │  ScalerCrop Control             │
       │  Selects region: (x,y,w,h)      │
       └─────────────────────────────────┘
       │
┌──────▼──────┐
│   Cropped   │  Selected region (e.g., 1000x750)
│   Region    │
└──────┬──────┘
       │
       ├─────────────────────────────────┐
       │  ISP Scaling                    │
       │  Scales to output size          │
       └─────────────────────────────────┘
       │
┌──────▼──────┐
│   Output    │  Your configured resolution (e.g., 640x480)
│   Stream    │
└─────────────┘
```

### Key Concepts

1. **Sensor Resolution**: The full resolution of your camera sensor. You can get this with:
   ```python
   sensor_res = picam2.camera_properties['PixelArraySize']
   ```

2. **Output Resolution**: The resolution you configure for your video stream:
   ```python
   config = picam2.create_video_configuration(main={"size": (640, 480)})
   ```

3. **Digital Zoom**: Achieved by reducing the crop window size while keeping it centered.
   - Smaller crop = More zoomed in
   - Larger crop = Zoomed out

4. **Pan/Tilt**: Achieved by moving the crop window position (x, y) while maintaining size.
   - Increase x = Pan right
   - Decrease x = Pan left
   - Increase y = Pan down
   - Decrease y = Pan up

5. **Aspect Ratio**: The crop region should maintain the same aspect ratio as your output resolution to avoid distortion.

## Implementation Steps

### Step 1: Get Sensor Information

```python
from picamera2 import Picamera2

picam2 = Picamera2()

# Get full sensor resolution
sensor_width, sensor_height = picam2.camera_properties['PixelArraySize']

# Check available sensor MODES (not crops) and their max framerates
# These are hardware-level sensor configurations (binning/subsampling)
for mode in picam2.sensor_modes:
    print(f"Mode: {mode['size']}, Max FPS: {mode['fps']}")
# Example output for IMX708:
# Mode: (4056, 3040), Max FPS: 18.0  <- Full sensor readout
# Mode: (2028, 1520), Max FPS: 40.0  <- 2x2 binned (less data to read)
# Mode: (1014, 760), Max FPS: 120.0  <- 4x4 binned (even less data)

# Get available ScalerCrop range for ePTZ
min_crop, max_crop, default_crop = picam2.camera_controls['ScalerCrop']
print(f"Sensor resolution: {sensor_width}x{sensor_height}")
print(f"Max crop region: {max_crop}")
```

**Key Insight**: 
- **Sensor modes** are hardware configurations that determine framerate
- **ScalerCrop** is a software crop applied AFTER sensor readout (ePTZ)
- To get wide view at high FPS, you're limited by available sensor modes

### Step 2: Configure Camera for Wide View with Full Sensor

```python
# OPTION 1: Full sensor mode with ePTZ - Wide FOV, Lower FPS
# This gives you the FULL sensor resolution to work with for ePTZ
# Framerate will be ~18 FPS (determined by full sensor mode)
config = picam2.create_video_configuration(
    main={"size": (640, 480)},  # Output: 480p (ISP scales for free)
    raw={}  # Use full sensor mode
)
picam2.configure(config)
picam2.start()

# Now you can use ScalerCrop for ePTZ anywhere in the full 4056x3040 sensor
# This does NOT affect framerate - still ~18 FPS

# OPTION 2: Binned sensor mode - Smaller FOV, Higher FPS
# This sacrifices field of view at the hardware level for speed
fast_mode = next(m for m in picam2.sensor_modes if m['fps'] > 100)
config = picam2.create_video_configuration(
    main={"size": (640, 480)},  # Output: still 480p
    raw={"size": fast_mode['size'], "format": fast_mode['format'].format}
)
picam2.configure(config)
picam2.start()
# Now you have ~120 FPS, but only ~1014x760 sensor area to work with
```

**Answer to your question**: Yes! You CAN read the entire sensor with `ScalerCrop` and output 480p. You'll get the full wide view at the sensor's native framerate (~18 FPS for 12MP). The ISP scaling is free.

### Step 3: Calculate Crop Region

```python
def calculate_crop(sensor_width, sensor_height, output_width, output_height, 
                   zoom_factor=1.0, pan_x=0.5, pan_y=0.5):
    """
    Calculate ScalerCrop values for ePTZ.
    
    Args:
        sensor_width: Full sensor width in pixels
        sensor_height: Full sensor height in pixels
        output_width: Desired output width
        output_height: Desired output height
        zoom_factor: Zoom level (1.0 = no zoom, 2.0 = 2x zoom, etc.)
        pan_x: Horizontal position (0.0 = left, 0.5 = center, 1.0 = right)
        pan_y: Vertical position (0.0 = top, 0.5 = center, 1.0 = bottom)
    
    Returns:
        Tuple of (x, y, width, height) for ScalerCrop
    """
    # Calculate aspect ratio
    output_aspect = output_width / output_height
    sensor_aspect = sensor_width / sensor_height
    
    # Calculate crop dimensions based on zoom
    crop_width = int(sensor_width / zoom_factor)
    crop_height = int(sensor_height / zoom_factor)
    
    # Maintain aspect ratio
    if output_aspect > sensor_aspect:
        # Output is wider - constrain by width
        crop_height = int(crop_width / output_aspect)
    else:
        # Output is taller - constrain by height  
        crop_width = int(crop_height * output_aspect)
    
    # Calculate position based on pan values
    max_x = sensor_width - crop_width
    max_y = sensor_height - crop_height
    
    x = int(max_x * pan_x)
    y = int(max_y * pan_y)
    
    # Ensure even values (required by camera)
    x = (x // 2) * 2
    y = (y // 2) * 2
    crop_width = (crop_width // 2) * 2
    crop_height = (crop_height // 2) * 2
    
    return (x, y, crop_width, crop_height)
```

### Step 4: Apply Crop Region

```python
# Example: 2x zoom, centered
crop = calculate_crop(sensor_width, sensor_height, 640, 480, zoom_factor=2.0)
picam2.set_controls({"ScalerCrop": crop})

# Example: Pan to top-left corner at 1.5x zoom
crop = calculate_crop(sensor_width, sensor_height, 640, 480, 
                     zoom_factor=1.5, pan_x=0.25, pan_y=0.25)
picam2.set_controls({"ScalerCrop": crop})
```

### Step 5: Smooth Transitions

For smooth ePTZ movements, update the crop region gradually:

```python
import time

def smooth_zoom(picam2, sensor_size, output_size, start_zoom, end_zoom, duration, steps=30):
    """Smoothly transition between zoom levels."""
    for i in range(steps + 1):
        progress = i / steps
        current_zoom = start_zoom + (end_zoom - start_zoom) * progress
        
        crop = calculate_crop(
            sensor_size[0], sensor_size[1],
            output_size[0], output_size[1],
            zoom_factor=current_zoom
        )
        
        picam2.set_controls({"ScalerCrop": crop})
        time.sleep(duration / steps)
```

## Important Considerations

### 1. Coordinate Systems

The picamera2 library handles multiple coordinate systems:
- **Sensor coordinates**: Full sensor resolution
- **ScalerCrop coordinates**: In sensor pixel space
- **Output coordinates**: Your configured output resolution
- **ISP coordinates**: Internal scaling stage

The `ScalerCrop` control always uses **sensor coordinates**, regardless of your output resolution.

### 2. Performance

- **No additional processing overhead**: The ISP (Image Signal Processor) handles scaling in hardware
- **Framerate determined by sensor mode, NOT ScalerCrop**: 
  - **Sensor mode** (hardware binning/subsampling) determines the framerate
  - **ScalerCrop** (ePTZ) does NOT change framerate - it's applied AFTER sensor readout
  - If you use full sensor mode, you get full sensor framerate (~18 FPS for 12MP) **regardless of ScalerCrop**
  - The ISP can scale any crop size to any output resolution with zero overhead
- **Example with IMX708 (12MP sensor) - Full Sensor Mode**:
  - Sensor mode: 4056x3040 (full sensor)
  - Maximum framerate: ~18 FPS
  - ScalerCrop: ANY crop size (full, half, quarter) → Still ~18 FPS
  - Output resolution: ANY size (4K, 1080p, 480p) → Still ~18 FPS
  - **You can use the full sensor AND get 480p output, but still at 18 FPS**
- **To get high FPS (60-120), you MUST use a binned/subsampled sensor mode**:
  - This sacrifices field of view at the sensor level
  - See "High-Speed ePTZ" example below
- **Quality**: ePTZ zooming reduces effective resolution but does NOT affect framerate

### 3. Limitations

- **Minimum crop size**: There are hardware limits on how small the crop can be (zoom limit)
- **Must maintain aspect ratio**: To avoid distortion
- **Even values required**: All dimensions must be even numbers
- **Bounds checking**: Ensure crop region stays within sensor bounds

### 4. Reading Current Crop

You can read the current crop from metadata:

```python
metadata = picam2.capture_metadata()
current_crop = metadata['ScalerCrop']
print(f"Current crop: {current_crop}")  # (x, y, width, height)
```

### 5. Platform Differences

- **Pi 4 (VC4 platform)**: Limited support for different crops on main and lores streams
- **Pi 5 (PISP platform)**: Full support for independent crops via `ScalerCrops` control

## Common Use Cases

### Security Camera with Region of Interest

```python
# Monitor a specific area at higher effective resolution
crop = calculate_crop(
    sensor_width, sensor_height, 640, 480,
    zoom_factor=3.0,  # 3x zoom
    pan_x=0.7,  # Focus on right side
    pan_y=0.3   # Focus on upper area
)
picam2.set_controls({"ScalerCrop": crop})
```

### Follow Object

```python
def follow_object(picam2, sensor_size, output_size, object_x, object_y, zoom=2.0):
    """Center crop on detected object position."""
    # Normalize object position to 0.0-1.0 range
    pan_x = object_x / output_size[0]
    pan_y = object_y / output_size[1]
    
    crop = calculate_crop(
        sensor_size[0], sensor_size[1],
        output_size[0], output_size[1],
        zoom_factor=zoom,
        pan_x=pan_x,
        pan_y=pan_y
    )
    
    picam2.set_controls({"ScalerCrop": crop})
```

### Cinematic Zoom Effect

```python
# Slowly zoom in on subject
smooth_zoom(picam2, (4056, 3040), (640, 480), 
           start_zoom=1.0, end_zoom=4.0, duration=5.0)
```

### High-Speed ePTZ (90-120 FPS)

**IMPORTANT**: To achieve high framerates, you MUST sacrifice field of view by using a binned/subsampled **sensor mode**. ScalerCrop (ePTZ) does NOT change the sensor readout speed.

```python
# Find the fastest sensor mode (hardware binning/subsampling)
available_modes = picam2.sensor_modes
available_modes.sort(key=lambda x: x["fps"], reverse=True)
fast_mode = available_modes[0]  # Highest FPS mode
print(f"Using mode: {fast_mode['size']} at {fast_mode['fps']} FPS")
# Example: (1014, 760) at 120 FPS

# Configure camera with fast sensor mode
config = picam2.create_video_configuration(
    main={"size": (640, 480)},  # Output resolution
    raw={"size": fast_mode['size'], "format": fast_mode['format'].format}  # Fast sensor mode
)
picam2.configure(config)

# Set maximum framerate
picam2.set_controls({"FrameRate": fast_mode['fps']})
picam2.start()

# Now you have 120 FPS, but ONLY a 1014x760 sensor area
# You can still do ePTZ within this smaller area
sensor_w, sensor_h = fast_mode['size']

# Example: Zoom 1.5x within the already-small sensor area
crop = calculate_crop(sensor_w, sensor_h, 640, 480, zoom_factor=1.5)
picam2.set_controls({"ScalerCrop": crop})
# Still 120 FPS - ScalerCrop doesn't affect framerate
```

**Trade-offs**:
- ✅ Very high framerate (60-120 FPS)
- ✅ Lower latency
- ✅ Can still do ePTZ within the smaller sensor area
- ❌ **Reduced field of view** (sensor only reads small area)
- ❌ Less total zoom range available (smaller area to crop from)

**The Limitation**: There's no way to get full sensor FOV (4056x3040) at high FPS - the hardware physically can't read 12MP that fast. You must choose between:
1. **Wide FOV** (full sensor) at **low FPS** (~18 FPS) - use full sensor mode
2. **Narrow FOV** (binned sensor) at **high FPS** (~120 FPS) - use binned sensor mode

### FPV Drone Use Case

**For FPV drones, high framerate is CRITICAL for low latency. Accept the narrower FOV.**

```python
from picamera2 import Picamera2
import time

picam2 = Picamera2()

# FPV Configuration: Prioritize framerate over FOV
# Find fastest available sensor mode
available_modes = picam2.sensor_modes
available_modes.sort(key=lambda x: x["fps"], reverse=True)
fpv_mode = available_modes[0]

print(f"FPV Mode: {fpv_mode['size']} at {fpv_mode['fps']} FPS")
print(f"Frame latency: {1000/fpv_mode['fps']:.1f}ms")

# Configure for low-latency FPV
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "XRGB8888"},  # 480p is sufficient for FPV
    raw={"size": fpv_mode['size'], "format": fpv_mode['format'].format},
    buffer_count=2  # Minimize buffering for low latency
)
picam2.configure(config)

# Disable auto-exposure/white balance for consistent latency
picam2.set_controls({
    "FrameRate": fpv_mode['fps'],
    "AeEnable": False,
    "AwbEnable": False,
    "ExposureTime": 5000,  # Fixed exposure (5ms)
    "AnalogueGain": 2.0,   # Fixed gain
})

picam2.start()

# Optional: Use ePTZ to adjust view within the binned sensor area
sensor_w, sensor_h = fpv_mode['size']

# Center crop with slight zoom for better framing
crop = calculate_crop(sensor_w, sensor_h, 640, 480, zoom_factor=1.2)
picam2.set_controls({"ScalerCrop": crop})

# Stream to FPV goggles/transmitter
# ... your streaming code here ...
```

**FPV Recommendations**:
- ✅ Use fastest sensor mode (60-120 FPS)
- ✅ 480p output is sufficient (640x480 or 720x480)
- ✅ `buffer_count=2` for minimal latency
- ✅ Disable AE/AWB for consistent frame timing
- ✅ Fixed exposure/gain prevents frame drops
- ⚠️ Accept narrower FOV - latency is more important
- ⚠️ Limited ePTZ range due to smaller sensor readout area

**Latency Comparison**:
- Full sensor (18 FPS): ~55ms between frames ❌ Too laggy for FPV
- 2x2 binned (40 FPS): ~25ms between frames ⚠️ Borderline
- 4x4 binned (120 FPS): ~8ms between frames ✅ Good for FPV

## Example Code

See `examples/eptz_demo.py` for a complete working example with:
- Interactive zoom control
- Pan/tilt navigation
- Smooth transitions
- Real-time display

## API Reference

### Controls

- **ScalerCrop**: `(x, y, width, height)` - Set crop region in sensor coordinates
- **ScalerCrops**: List of crop regions for multi-stream configurations (Pi 5 only)

### Properties

- **PixelArraySize**: Full sensor resolution `(width, height)`
- **camera_controls['ScalerCrop']**: Returns `(min, max, default)` crop values

### Methods

- `picam2.set_controls({"ScalerCrop": (x, y, w, h)})`: Apply crop
- `picam2.capture_metadata()['ScalerCrop']`: Read current crop
- `picam2.camera_properties['PixelArraySize']`: Get sensor size

## Troubleshooting

**Distorted image**: Check that crop aspect ratio matches output aspect ratio

**Crop not applying**: Ensure:
- All values are even numbers
- Crop region is within sensor bounds
- Camera is started before setting controls

**Jerky movement**: Increase number of steps in smooth transitions

**Black borders**: Crop aspect ratio doesn't match output - adjust calculation

## Further Reading

- `examples/zoom.py` - Simple zoom example
- `apps/app_full.py` - Full application with pan/zoom GUI
- `controls.py` - Control system documentation
- libcamera documentation on ScalerCrop

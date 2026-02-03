# ePTZ Implementation Summary

## What I've Created

I've analyzed the picamera2 library and created a comprehensive guide and examples for implementing electronic Pan-Tilt-Zoom (ePTZ). Here's what you now have:

## Files Created

### 1. **ePTZ_guide.md** (Main Documentation)
A comprehensive guide explaining:
- How ePTZ works in picamera2
- The signal path from sensor to output
- The ScalerCrop control mechanism
- Step-by-step implementation instructions
- Coordinate systems and transformations
- Performance considerations and limitations
- Common use cases
- API reference
- Troubleshooting tips

### 2. **examples/eptz_demo.py** (Interactive Demo)
Full-featured interactive demo with:
- Keyboard controls for pan, tilt, and zoom
- Smooth transitions between positions
- Preset positions (corners, center)
- Real-time status display
- Both interactive and automated modes
- ePTZController class for easy integration

**Usage:**
```bash
python examples/eptz_demo.py          # Interactive mode
python examples/eptz_demo.py auto     # Automated demo
```

### 3. **examples/eptz_simple.py** (Basic Example)
Simple, easy-to-understand example showing:
- How to get sensor information
- How to configure for lower output resolution
- Basic crop calculation
- Various zoom and pan examples
- Smooth zoom and pan demonstrations

**Usage:**
```bash
python examples/eptz_simple.py
```

### 4. **examples/eptz_tracking.py** (Object Tracking)
Advanced example demonstrating:
- Automatic object tracking with ePTZ
- Smooth following of moving objects
- Dynamic zoom based on object size
- Simulated object detection (can be replaced with real detection)
- Practical application for security/monitoring

**Usage:**
```bash
python examples/eptz_tracking.py
```

### 5. **examples/eptz_recording.py** (Video Recording)
Video recording with ePTZ effects:
- Cinematic zoom and pan effects
- Security patrol pattern simulation
- Recording 480p from high-res sensor
- Smooth transitions during recording
- Multiple recording modes

**Usage:**
```bash
python examples/eptz_recording.py cinematic [duration] [output.mp4]
python examples/eptz_recording.py security [duration] [output.mp4]
```

## How ePTZ Works in Picamera2

### Key Mechanism: ScalerCrop Control

The `ScalerCrop` control is a tuple of 4 values: `(x, y, width, height)`

```python
# Example: 2x zoom, centered
sensor_width, sensor_height = picam2.camera_properties['PixelArraySize']
crop_width = sensor_width // 2
crop_height = sensor_height // 2
x = (sensor_width - crop_width) // 2
y = (sensor_height - crop_height) // 2

picam2.set_controls({"ScalerCrop": (x, y, crop_width, crop_height)})
```

### Signal Flow

```
Full Sensor (4K)
    ↓
ScalerCrop (selects region)
    ↓
ISP Scaling (hardware)
    ↓
Output Stream (480p)
```

### Code Path in Library

1. **Controls.py** - `ScalerCrop` is handled as a control
   - `set_controls()` method accepts the ScalerCrop tuple
   - Converts to libcamera Rectangle type
   - Applies to camera hardware

2. **Picamera2.py** - Main configuration and control flow
   - `create_video_configuration()` sets up output resolution
   - `set_controls()` applies ScalerCrop at runtime
   - `capture_metadata()` can read current crop

3. **Hardware ISP** - Does the actual work
   - Reads specified region from sensor
   - Scales to output resolution
   - No CPU overhead (hardware acceleration)

## Your Use Case: 4K Sensor → 480p Output with ePTZ

### Quick Start Code

```python
from picamera2 import Picamera2

picam2 = Picamera2()

# Get sensor resolution (e.g., 4056x3040 for IMX708)
sensor_w, sensor_h = picam2.camera_properties['PixelArraySize']

# Configure for 480p output
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

# Apply 2x zoom, centered
crop_w = sensor_w // 2
crop_h = sensor_h // 2
crop_x = (sensor_w - crop_w) // 2
crop_y = (sensor_h - crop_h) // 2

picam2.set_controls({"ScalerCrop": (crop_x, crop_y, crop_w, crop_h)})
```

### Important Considerations

1. **Coordinates are in sensor space** - Always use full sensor resolution for calculations
2. **Must be even numbers** - All crop values must be divisible by 2
3. **Maintain aspect ratio** - Crop aspect should match output aspect to avoid distortion
4. **No performance penalty** - ISP does scaling in hardware
5. **Real-time adjustable** - Can change crop on every frame if needed

## Practical Applications

### 1. Security Camera
```python
# Focus on doorway at 3x zoom
crop = calculate_crop(sensor_size, output_size, 
                     zoom_factor=3.0, pan_x=0.7, pan_y=0.3)
picam2.set_controls({"ScalerCrop": crop})
```

### 2. Object Following
```python
# Track detected person
for frame in video_stream:
    person_x, person_y = detect_person(frame)
    crop = calculate_crop_for_position(person_x, person_y, zoom=2.0)
    picam2.set_controls({"ScalerCrop": crop})
```

### 3. Video Conference
```python
# Keep speaker centered and framed
speaker_bbox = detect_face(frame)
crop = auto_frame_object(speaker_bbox, zoom=1.8)
picam2.set_controls({"ScalerCrop": crop})
```

## Integration with Your Code

### Option 1: Use ePTZController Class
```python
from eptz_demo import ePTZController

picam2 = Picamera2()
# ... configure and start ...

controller = ePTZController(picam2, output_size=(640, 480))
controller.zoom_in()
controller.pan_right()
controller.apply_crop()
```

### Option 2: Use Helper Function
```python
def calculate_crop(sensor_w, sensor_h, output_w, output_h, zoom, pan_x, pan_y):
    # See eptz_simple.py for full implementation
    pass

crop = calculate_crop(sensor_width, sensor_height, 640, 480, 
                     zoom_factor=2.0, pan_x=0.5, pan_y=0.5)
picam2.set_controls({"ScalerCrop": crop})
```

### Option 3: Direct Control
```python
# Manual calculation
zoom = 2.0
crop_w = int(sensor_width / zoom)
crop_h = int(sensor_height / zoom)
crop_x = (sensor_width - crop_w) // 2
crop_y = (sensor_height - crop_h) // 2

picam2.set_controls({"ScalerCrop": (crop_x, crop_y, crop_w, crop_h)})
```

## Testing Your Implementation

1. **Run the simple example first:**
   ```bash
   python examples/eptz_simple.py
   ```

2. **Try interactive control:**
   ```bash
   pip install readchar
   python examples/eptz_demo.py
   ```

3. **Test with your own code:**
   - Copy the `calculate_crop()` function
   - Adjust for your specific needs
   - Test different zoom levels and positions

## Next Steps

1. **Read** `ePTZ_guide.md` for detailed explanations
2. **Run** `eptz_simple.py` to see basic functionality
3. **Experiment** with `eptz_demo.py` for interactive control
4. **Study** `eptz_tracking.py` for tracking implementation
5. **Integrate** into your application using examples as reference

## Key Library Files (for reference)

- `picamera2/controls.py` - Control handling (line 65-92)
- `picamera2/picamera2.py` - Main API (line 838+ for video config)
- `examples/zoom.py` - Original simple zoom example
- `apps/app_full.py` - Full GUI app with pan/zoom (lines 515-600)

## Questions?

The guide and examples should cover most use cases. If you need:
- **More zoom range**: Adjust `max_zoom` in ePTZController
- **Faster transitions**: Increase `smoothing` parameter
- **Different aspect ratios**: Modify crop calculation
- **Integration with AI**: See `eptz_tracking.py` as template

All examples are fully documented with inline comments explaining each step!

# ePTZ Quick Reference Card

## Essential Concepts

### What is ePTZ?
Electronic Pan-Tilt-Zoom: Digitally crop and scale sensor regions to simulate camera movement without physical mechanisms.

### Why Use ePTZ?
- Use 4K sensor, output 480p video
- Extract regions of interest
- Track objects automatically
- No moving parts needed
- Hardware-accelerated (no CPU cost)

## Core API

### Get Sensor Info
```python
from picamera2 import Picamera2
picam2 = Picamera2()

# Full sensor resolution
sensor_w, sensor_h = picam2.camera_properties['PixelArraySize']

# Crop limits
min_crop, max_crop, default_crop = picam2.camera_controls['ScalerCrop']
```

### Configure Camera
```python
# Output at 480p
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()
```

### Set Crop Region
```python
# (x, y, width, height) in sensor coordinates
picam2.set_controls({"ScalerCrop": (x, y, width, height)})
```

### Read Current Crop
```python
metadata = picam2.capture_metadata()
current_crop = metadata['ScalerCrop']  # (x, y, w, h)
```

## Quick Calculations

### 2x Zoom (Centered)
```python
crop_w = sensor_w // 2
crop_h = sensor_h // 2
x = (sensor_w - crop_w) // 2
y = (sensor_h - crop_h) // 2
picam2.set_controls({"ScalerCrop": (x, y, crop_w, crop_h)})
```

### Zoom to Factor
```python
def zoom(factor):
    crop_w = int(sensor_w / factor)
    crop_h = int(sensor_h / factor)
    x = (sensor_w - crop_w) // 2
    y = (sensor_h - crop_h) // 2
    # Make even
    x, y = (x//2)*2, (y//2)*2
    crop_w, crop_h = (crop_w//2)*2, (crop_h//2)*2
    return (x, y, crop_w, crop_h)
```

### Pan to Position
```python
def pan_to(pan_x, pan_y, zoom=1.0):
    """pan_x, pan_y: 0.0 to 1.0 (0.5 = center)"""
    crop_w = int(sensor_w / zoom)
    crop_h = int(sensor_h / zoom)
    x = int((sensor_w - crop_w) * pan_x)
    y = int((sensor_h - crop_h) * pan_y)
    # Make even
    x, y = (x//2)*2, (y//2)*2
    crop_w, crop_h = (crop_w//2)*2, (crop_h//2)*2
    return (x, y, crop_w, crop_h)
```

### Maintain Aspect Ratio
```python
def calculate_crop(sensor_w, sensor_h, output_w, output_h, zoom, pan_x, pan_y):
    output_aspect = output_w / output_h
    
    crop_w = int(sensor_w / zoom)
    crop_h = int(sensor_h / zoom)
    
    # Adjust for aspect ratio
    if crop_w / crop_h > output_aspect:
        crop_w = int(crop_h * output_aspect)
    else:
        crop_h = int(crop_w / output_aspect)
    
    # Position
    x = int((sensor_w - crop_w) * pan_x)
    y = int((sensor_h - crop_h) * pan_y)
    
    # Make even & clamp
    x = max(0, (x//2)*2)
    y = max(0, (y//2)*2)
    crop_w = (crop_w//2)*2
    crop_h = (crop_h//2)*2
    
    return (x, y, crop_w, crop_h)
```

## Common Patterns

### Center + Zoom
```python
crop = calculate_crop(sensor_w, sensor_h, 640, 480, 
                     zoom=2.0, pan_x=0.5, pan_y=0.5)
picam2.set_controls({"ScalerCrop": crop})
```

### Top-Left Corner
```python
crop = calculate_crop(sensor_w, sensor_h, 640, 480,
                     zoom=1.5, pan_x=0.25, pan_y=0.25)
picam2.set_controls({"ScalerCrop": crop})
```

### Follow Object
```python
# object_x, object_y in output coordinates (0-640, 0-480)
pan_x = object_x / 640
pan_y = object_y / 480
crop = calculate_crop(sensor_w, sensor_h, 640, 480,
                     zoom=2.0, pan_x=pan_x, pan_y=pan_y)
picam2.set_controls({"ScalerCrop": crop})
```

### Smooth Zoom
```python
import time

for zoom in [1.0, 1.2, 1.5, 2.0, 2.5, 3.0]:
    crop = calculate_crop(sensor_w, sensor_h, 640, 480,
                         zoom=zoom, pan_x=0.5, pan_y=0.5)
    picam2.set_controls({"ScalerCrop": crop})
    time.sleep(0.2)
```

## Coordinate Systems

| System | Description | Example |
|--------|-------------|---------|
| Sensor | Full sensor resolution | 4056x3040 |
| ScalerCrop | Region in sensor space | (1000, 750, 2056, 1540) |
| Output | Your video resolution | 640x480 |

**Important:** ScalerCrop always uses sensor coordinates!

## Common Values (IMX708 Sensor)

| Zoom | Crop Size | Center Position |
|------|-----------|-----------------|
| 1.0x | 4056x3040 | (0, 0) |
| 1.5x | 2704x2026 | (676, 507) |
| 2.0x | 2028x1520 | (1014, 760) |
| 3.0x | 1352x1013 | (1352, 1013) |
| 4.0x | 1014x760  | (1521, 1140) |

## Rules & Constraints

✅ **DO:**
- Use even numbers for all values
- Stay within sensor bounds
- Maintain aspect ratio
- Update every frame if needed

❌ **DON'T:**
- Use odd numbers (hardware requires even)
- Exceed sensor dimensions
- Mix coordinate systems
- Forget to clamp values

## Performance

- ✅ **Hardware accelerated** - ISP does the work
- ✅ **Zero CPU overhead** - No performance penalty
- ✅ **Full framerate** - No slowdown
- ✅ **Real-time updates** - Change every frame

## Examples

### Minimal Example
```python
from picamera2 import Picamera2

picam2 = Picamera2()
sensor_w, sensor_h = picam2.camera_properties['PixelArraySize']

config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

# 2x zoom
crop = (sensor_w//4, sensor_h//4, sensor_w//2, sensor_h//2)
picam2.set_controls({"ScalerCrop": crop})
```

### Complete Files
- `examples/eptz_simple.py` - Basic usage
- `examples/eptz_demo.py` - Interactive control
- `examples/eptz_tracking.py` - Object tracking
- `examples/eptz_recording.py` - Video recording

## Debugging

### Check Current Crop
```python
metadata = picam2.capture_metadata()
print(f"Current crop: {metadata['ScalerCrop']}")
```

### Verify Sensor Size
```python
sensor_size = picam2.camera_properties['PixelArraySize']
print(f"Sensor: {sensor_size}")
```

### Check if Crop is Valid
```python
x, y, w, h = crop
assert x >= 0 and y >= 0
assert x + w <= sensor_w
assert y + h <= sensor_h
assert x % 2 == 0 and y % 2 == 0
assert w % 2 == 0 and h % 2 == 0
```

## Common Issues

**Distorted Image?**
→ Crop aspect ratio ≠ output aspect ratio

**Crop Not Working?**
→ Check values are even, within bounds

**Jerky Movement?**
→ Add interpolation between positions

**Black Borders?**
→ Aspect ratio mismatch

## Resources

- **Guide:** `ePTZ_guide.md`
- **Summary:** `ePTZ_SUMMARY.md`
- **Examples:** `examples/eptz_*.py`
- **Library:** `picamera2/controls.py`

---

**Quick Start:** `python examples/eptz_simple.py`

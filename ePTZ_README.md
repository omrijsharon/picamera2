# Electronic Pan-Tilt-Zoom (ePTZ) Documentation

## Overview

This documentation package provides everything you need to implement electronic Pan-Tilt-Zoom (ePTZ) functionality using the picamera2 library. ePTZ allows you to use a high-resolution camera sensor (e.g., 4K) to output lower resolution video (e.g., 480p) while maintaining the ability to digitally pan, tilt, and zoom within the full sensor field of view.

## What You Get

This package includes:
- 📘 Comprehensive implementation guide
- 📝 Quick reference card  
- 🎯 Working code examples
- 🔧 Reusable components
- 💡 Best practices and tips

## Files in This Package

### Documentation

1. **ePTZ_guide.md** (⭐ START HERE)
   - Complete technical guide
   - How ePTZ works in picamera2
   - Step-by-step implementation
   - API reference
   - Troubleshooting

2. **ePTZ_SUMMARY.md**
   - Quick overview of all files
   - Integration instructions
   - Key code paths in library
   - Common use cases

3. **ePTZ_QUICK_REFERENCE.md**
   - Cheat sheet for quick lookup
   - Common code patterns
   - Calculation formulas
   - Debugging tips

### Examples (in `examples/` folder)

1. **eptz_simple.py** - Start here!
   - Basic ePTZ operations
   - Simple zoom and pan
   - Easy to understand
   - ~150 lines of code

2. **eptz_demo.py** - Interactive demo
   - Keyboard control (arrow keys, +/-, etc.)
   - ePTZController class
   - Smooth transitions
   - Both interactive and auto modes
   - ~350 lines of code

3. **eptz_tracking.py** - Object tracking
   - Automatic object following
   - Dynamic zoom
   - Smooth tracking
   - Template for AI integration
   - ~230 lines of code

4. **eptz_recording.py** - Video recording
   - Record with ePTZ effects
   - Cinematic zoom/pan
   - Security patrol pattern
   - ~280 lines of code

## Quick Start (5 Minutes)

### 1. Understand the Concept
```
High-Res Sensor (4K) → Select Region (ePTZ) → Output Video (480p)
```

### 2. Run the Simple Example
```bash
cd examples
python eptz_simple.py
```

This will show you 9 different ePTZ operations in sequence.

### 3. Try Interactive Control
```bash
pip install readchar  # For keyboard input
python eptz_demo.py
```

Use arrow keys to pan, +/- to zoom!

### 4. Read the Guide
Open `ePTZ_guide.md` for complete documentation.

## The Key Control: ScalerCrop

Everything revolves around one control:

```python
picam2.set_controls({"ScalerCrop": (x, y, width, height)})
```

Where:
- `x, y` = Position in sensor coordinates
- `width, height` = Size of crop region
- All values must be even numbers
- All values in full sensor pixel space

## Basic Usage Pattern

```python
from picamera2 import Picamera2

# 1. Initialize
picam2 = Picamera2()
sensor_w, sensor_h = picam2.camera_properties['PixelArraySize']

# 2. Configure for lower output resolution
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

# 3. Calculate crop region
zoom = 2.0  # 2x zoom
crop_w = int(sensor_w / zoom)
crop_h = int(sensor_h / zoom)
crop_x = (sensor_w - crop_w) // 2  # Centered
crop_y = (sensor_h - crop_h) // 2

# Make even (hardware requirement)
crop_x, crop_y = (crop_x//2)*2, (crop_y//2)*2
crop_w, crop_h = (crop_w//2)*2, (crop_h//2)*2

# 4. Apply crop
picam2.set_controls({"ScalerCrop": (crop_x, crop_y, crop_w, crop_h)})
```

## Use Cases

### Security Camera
Focus on specific area (doorway, window) at higher effective resolution:
```python
# Watch top-right corner at 3x zoom
crop = calculate_crop(sensor_w, sensor_h, 640, 480,
                     zoom=3.0, pan_x=0.75, pan_y=0.25)
picam2.set_controls({"ScalerCrop": crop})
```

### Video Conferencing
Keep speaker centered and properly framed:
```python
# Detect face position
face_x, face_y = detect_face(frame)

# Center on face with 2x zoom
pan_x = face_x / 640
pan_y = face_y / 480
crop = calculate_crop(sensor_w, sensor_h, 640, 480,
                     zoom=2.0, pan_x=pan_x, pan_y=pan_y)
picam2.set_controls({"ScalerCrop": crop})
```

### Sports/Action Recording
Follow moving subject automatically:
```python
# Track athlete
for frame in video:
    athlete_x, athlete_y = detect_athlete(frame)
    crop = follow_object(athlete_x, athlete_y, zoom=2.5)
    picam2.set_controls({"ScalerCrop": crop})
```

### Wildlife Monitoring
Monitor large area, zoom to activity:
```python
# Start wide
set_crop(zoom=1.0)

# Zoom to detected motion
if motion_detected:
    motion_x, motion_y = motion_location
    set_crop(zoom=3.0, pan_x=motion_x/640, pan_y=motion_y/480)
```

## Advantages of ePTZ

✅ **No Moving Parts** - Reliable, silent operation  
✅ **Hardware Accelerated** - Zero CPU overhead  
✅ **Full Framerate** - No performance penalty  
✅ **High Quality** - Uses full sensor capability  
✅ **Real-Time** - Instant response, no latency  
✅ **Flexible** - Change every frame if needed  
✅ **Cost Effective** - No motorized mount needed  

## Learning Path

### Beginner (30 minutes)
1. ✅ Read this README
2. ✅ Run `eptz_simple.py`
3. ✅ Review code in `eptz_simple.py`
4. ✅ Skim `ePTZ_QUICK_REFERENCE.md`

### Intermediate (1-2 hours)
1. ✅ Read `ePTZ_guide.md` sections 1-5
2. ✅ Run `eptz_demo.py` in interactive mode
3. ✅ Modify `eptz_simple.py` with your own values
4. ✅ Study the `calculate_crop()` function

### Advanced (3-4 hours)
1. ✅ Read full `ePTZ_guide.md`
2. ✅ Study `eptz_tracking.py` implementation
3. ✅ Run `eptz_recording.py`
4. ✅ Integrate ePTZController into your project
5. ✅ Add AI/CV for real object detection

## Integration Guide

### Option 1: Copy Helper Function
Copy `calculate_crop()` from `eptz_simple.py`:
```python
def calculate_crop(sensor_w, sensor_h, output_w, output_h, zoom, pan_x, pan_y):
    # ... implementation ...
    return (x, y, crop_w, crop_h)
```

### Option 2: Use ePTZController Class
Import from `eptz_demo.py`:
```python
from eptz_demo import ePTZController

controller = ePTZController(picam2, output_size=(640, 480))
controller.zoom_in()
controller.pan_right()
controller.apply_crop()
```

### Option 3: Build Your Own
Use the examples as reference and implement exactly what you need.

## Code Architecture

### How It Works in Picamera2

```
Your Code
    ↓
set_controls({"ScalerCrop": (x,y,w,h)})
    ↓
picamera2/controls.py - Validates control
    ↓
Converts to libcamera Rectangle
    ↓
Hardware ISP - Reads sensor region & scales
    ↓
Output stream at configured resolution
```

### Key Files in Library

- `picamera2/controls.py` - Control handling (lines 65-92)
- `picamera2/picamera2.py` - Main API (line 838+ for video config)
- Camera hardware ISP - Does actual cropping/scaling

## Common Questions

**Q: What's the maximum zoom?**  
A: Depends on sensor and output resolution. Typically 4-8x before quality degrades significantly.

**Q: Can I change crop every frame?**  
A: Yes! ePTZ has no performance penalty. Update as often as you want.

**Q: Does this work on all Raspberry Pi cameras?**  
A: Yes, works with any camera supported by picamera2.

**Q: What about Pi 4 vs Pi 5?**  
A: Both work. Pi 5 has more advanced features (ScalerCrops for multi-stream).

**Q: Can I use this with object detection?**  
A: Yes! See `eptz_tracking.py` for example integration.

**Q: Does zoom reduce quality?**  
A: You're using pixels from the full sensor, so quality is good. It's like digital zoom on any camera - you lose resolution but gain magnification.

## Performance Characteristics

- **CPU Usage:** 0% (hardware ISP)
- **Latency:** <1 frame
- **Frame Rate Impact:** None
- **Memory:** Minimal
- **Quality:** Excellent (uses full sensor)

## System Requirements

- Raspberry Pi with libcamera support
- Python 3.7+
- picamera2 library
- Optional: readchar (for interactive demo)

## Troubleshooting

### Image is distorted
→ Crop aspect ratio doesn't match output aspect ratio  
→ Use the `calculate_crop()` function which handles this

### Crop not applying
→ Check values are even numbers  
→ Verify crop is within sensor bounds  
→ Ensure camera is started before setting controls

### Jerky movement  
→ Add interpolation between positions  
→ See `smooth_transition()` in examples

### Black borders on output
→ Aspect ratio mismatch between crop and output  
→ Adjust crop calculation

## Further Reading

- **libcamera documentation** - Low-level camera control
- **examples/zoom.py** - Original simple zoom example
- **apps/app_full.py** - Full GUI with pan/zoom (lines 515-600)
- **Raspberry Pi camera documentation** - Camera modules

## Support & Community

- Study the provided examples
- Read the comprehensive guide
- Check the quick reference
- Review existing picamera2 examples

## Credits

This documentation was created by analyzing:
- picamera2 library source code
- Existing zoom and control examples
- libcamera ScalerCrop control
- Community use cases

## License

These documentation and examples follow the same license as the picamera2 library.

---

**Ready to start?** Run `python examples/eptz_simple.py` now!

**Need help?** Check `ePTZ_guide.md` for detailed explanations.

**Want quick answers?** See `ePTZ_QUICK_REFERENCE.md` for code snippets.

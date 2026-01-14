# OverlayHelper Quick Reference

## 30-Second Setup

```python
from picamera2 import Picamera2, Preview
from picamera2.overlay_helper import FPVOverlay
from libcamera import Transform

# Setup
picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)
stream = picam2.stream_map[config['display']]
hud = FPVOverlay(stream.configuration.size.width, 
                stream.configuration.size.height)

# Add elements
hud.add_crosshair()
hud.update_flight_mode("ACRO")

# Start
picam2.start_preview(Preview.QT, transform=Transform(transpose=1, vflip=1))
picam2.start()
picam2.set_overlay(hud.get_array())

# Update loop
while True:
    hud.update_battery(voltage, cell_count=3)
    hud.update_signal(rssi)
    picam2.set_overlay(hud.get_array())
```

## Common Methods

### Rectangles
```python
overlay.add_rectangle("name", x, y, width, height, (R, G, B, A))
overlay.add_rectangle("box", 10, 10, 100, 50, (255, 0, 0, 200), filled=True)
overlay.add_rectangle("outline", 10, 70, 100, 50, (0, 255, 0, 200), filled=False, thickness=2)
```

### Text (requires opencv-python)
```python
overlay.add_text("name", x, y, "Text", (R, G, B, A), font_scale=0.5, thickness=1)
overlay.update_text("voltage", 10, 30, "12.6V", (0, 255, 0, 255), font_scale=0.7, thickness=2)
```

### Lines (requires opencv-python)
```python
overlay.add_line("name", x1, y1, x2, y2, (R, G, B, A), thickness=2)
overlay.add_line("horizon", 0, 240, 640, 240, (0, 255, 0, 200), 2)
```

### Circles (requires opencv-python)
```python
overlay.add_circle("name", center_x, center_y, radius, (R, G, B, A), filled=True, thickness=2)
overlay.add_circle("target", 320, 240, 20, (255, 0, 0, 200), filled=False, thickness=2)
```

### FPV Helpers
```python
fpv.add_crosshair(size=25, color=(255, 0, 0, 200), thickness=2)
fpv.update_battery(voltage, cell_count=3, x=10, y=30)  # Auto color-coded
fpv.update_signal(rssi, x=10, y=60)                    # Auto color-coded (0-100)
fpv.update_flight_mode("ACRO", x=None, y=30)           # Defaults to top-right
```

### Management
```python
overlay.remove_element("name")      # Delete permanently
overlay.hide_element("name")        # Hide temporarily
overlay.show_element("name")        # Show again
overlay.clear_all()                 # Clear everything (use sparingly)
overlay.get_array()                 # Get numpy array (zero-copy)
overlay.get_stats()                 # {'elements': 5, 'updates': 120, ...}
```

### Method Chaining
```python
(overlay
    .add_crosshair()
    .update_battery(11.8)
    .update_signal(85)
    .update_flight_mode("ACRO"))

picam2.set_overlay(overlay.get_array())
```

## Color Format

RGBA tuples: `(Red, Green, Blue, Alpha)` where all values are 0-255

```python
(255, 0, 0, 255)     # Opaque red
(0, 255, 0, 200)     # Semi-transparent green
(255, 255, 255, 128) # Half-transparent white
(0, 0, 0, 0)         # Fully transparent (invisible)
```

## Common Colors

```python
# Solid colors
RED = (255, 0, 0, 255)
GREEN = (0, 255, 0, 255)
BLUE = (0, 0, 255, 255)
WHITE = (255, 255, 255, 255)
YELLOW = (255, 255, 0, 255)
CYAN = (0, 255, 255, 255)
MAGENTA = (255, 0, 255, 255)

# Semi-transparent (good for overlays)
RED_SEMI = (255, 0, 0, 200)
GREEN_SEMI = (0, 255, 0, 200)
WHITE_SEMI = (255, 255, 255, 200)

# Backgrounds
TRANSPARENT = (0, 0, 0, 0)
BLACK_SEMI = (0, 0, 0, 128)
```

## Performance

| Overlay Updates | Latency | Use Case |
|-----------------|---------|----------|
| 1-2 elements | <0.01ms | Minimal HUD |
| 3-5 elements | <0.05ms | Typical FPV |
| 10+ elements | <0.1ms | Full telemetry |

**Total latency**: Rotation (<0.2ms) + Overlay (<0.05ms) = **<0.25ms** ✅

## Tips

### Update Only What Changed
```python
# ✅ Good: Only update dynamic values
if voltage_changed:
    overlay.update_battery(voltage)
    picam2.set_overlay(overlay.get_array())

# ❌ Bad: Update everything every frame
overlay.clear_all()
overlay.add_crosshair()  # Static, doesn't need updating
overlay.update_battery(voltage)
```

### Pre-compute Static Values
```python
# ✅ Good: Compute once
COLOR_GREEN = (0, 255, 0, 255)
overlay.update_text("status", 10, 30, "OK", COLOR_GREEN)

# ❌ Bad: Recreate every frame
overlay.update_text("status", 10, 30, "OK", (0, 255, 0, 255))
```

### Use Appropriate Frequencies
```python
# Critical: 30-60 Hz
hud.update_battery(voltage)

# Normal: 10-20 Hz
hud.update_signal(rssi)

# Low: 1-5 Hz
hud.update_text("timer", 10, 90, f"{seconds}s", color)
```

## Install OpenCV (Optional but Recommended)

```bash
pip install opencv-python
```

Without OpenCV:
- ✅ Rectangles work
- ⚠️ Lines → rectangles (fallback)
- ⚠️ Circles → squares (fallback)
- ❌ Text not available

## Examples

```bash
python examples/fpv_minimal.py                  # Simplest setup
python examples/test_overlay_helper.py          # Full demo with stats
python examples/test_overlay_performance.py     # Performance comparison
```

## Documentation

Full documentation: `examples/OVERLAY_HELPER_README.md`

## Quick Debug

```python
# Check stats
stats = overlay.get_stats()
print(stats)
# {'elements': 5, 'updates': 120, 'size': '640x480', 'memory_mb': 1.17}

# Check element exists
if "battery" in overlay.elements:
    print("Battery element exists")

# Time an update
import time
start = time.perf_counter()
overlay.update_battery(11.8)
picam2.set_overlay(overlay.get_array())
print(f"Update took: {(time.perf_counter() - start) * 1000:.3f}ms")
```

import fcntl
import os
from enum import Enum

try:
    import videodev2  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    videodev2 = None


class Platform(Enum):
    VC4 = 0
    PISP = 1


_platform = Platform.VC4

# If videodev2 isn't present, we can't probe V4L2 capabilities here.
# Defaulting to VC4 is safe; callers can still override behavior elsewhere.
if videodev2 is not None:
    try:
        for num in range(64):
            device = '/dev/video' + str(num)
            if os.path.exists(device):
                with open(device, 'rb+', buffering=0) as fd:
                    caps = videodev2.v4l2_capability()
                    fcntl.ioctl(fd, videodev2.VIDIOC_QUERYCAP, caps)
                    decoded = videodev2.arr_to_str(caps.card)
                    if decoded == "pispbe":
                        _platform = Platform.PISP
                        break
                    elif decoded == "bcm2835-isp":
                        break
    except Exception:
        pass


def get_platform():
    return _platform

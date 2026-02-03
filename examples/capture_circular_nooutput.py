#!/usr/bin/python3
import time
from picamera2_contrib import Picamera2
from picamera2_contrib.encoders import H264Encoder
from picamera2_contrib.outputs import CircularOutput

picam2 = Picamera2()
fps = 30
dur = 5
micro = int((1 / fps) * 1000000)
vconfig = picam2.create_video_configuration()
vconfig['controls']['FrameDurationLimits'] = (micro, micro)
picam2.configure(vconfig)
encoder = H264Encoder()
output = CircularOutput(buffersize=int(fps * (dur + 0.2)), outputtofile=False)
output.fileoutput = "file.h264"
picam2.start_recording(encoder, output)
time.sleep(dur)
output.stop()

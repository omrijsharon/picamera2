#!/usr/bin/python3
import time
from picamera2_contrib import Picamera2
from picamera2_contrib.encoders import H264Encoder
from picamera2_contrib.outputs import FfmpegOutput

picam2 = Picamera2()
video_config = picam2.create_video_configuration()
picam2.configure(video_config)

encoder = H264Encoder(10000000)
output = FfmpegOutput('test.mp4', audio=True)

picam2.start_recording(encoder, output)
time.sleep(10)
picam2.stop_recording()

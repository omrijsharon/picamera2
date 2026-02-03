#!/usr/bin/python3
import time
from picamera2_contrib import Picamera2
from picamera2_contrib.encoders import Encoder
from picamera2_contrib.outputs import Output

picam2 = Picamera2()
picam2.configure()
encoder = Encoder()
output = Output()
picam2.start_recording(encoder, output)
time.sleep(5)
picam2.stop_recording()

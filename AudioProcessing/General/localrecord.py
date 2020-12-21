import pyaudio
import struct
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import wave
import math
import time
import json

mic = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 8192
stream = mic.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                  input_device_index=3,
                  input=True, frames_per_buffer=CHUNK)

'''
Built-in Input
Built-in Output
DisplayPort
SteelSeries Arctis 1 Wireless
MMAudio Device
MMAudio Device (UI Sounds)
Soundflower (2ch)
Soundflower (64ch)
ZoomAudioDevice
Quicktime Input
Screen Record Audio
'''


init = time.time()
fm = []

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        fm.append(data)
except KeyboardInterrupt:
    pass

wf = wave.open('localrecord.wav', 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(2)
wf.setframerate(RATE)
wf.writeframes(b''.join(fm))
wf.close()

stream.stop_stream()
stream.close()
mic.terminate()

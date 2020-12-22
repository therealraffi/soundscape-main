import pyaudio
import struct
import matplotlib.pyplot as plt
import numpy as np
import wave
import math
import time
import json
import noisereduce as nr
from scipy.io import wavfile
import librosa

mic = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 8192
stream = mic.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                  input_device_index=0,
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

t1 = time.time()

print("start")
fb = []
bint = np.array([], dtype=np.int16)
while(time.time() - t1 < 1):
    data = stream.read(CHUNK, exception_on_overflow=False)
    fb.append(data)
    data = np.frombuffer(data, dtype=np.int16)
    bint = np.append(bint, data)
    pass
print(bint, len(bint), min(bint), max(bint))
init = time.time()
fm = []
fint = np.array([], dtype=np.int16)
print("start main")
try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        fm.append(data)
        data = np.frombuffer(data, dtype=np.int16)
        fint = np.append(fint, data)
except KeyboardInterrupt:
    pass

print()
print("filter")
reduced_noise = nr.reduce_noise(audio_clip=fint.astype('float32'), noise_clip=bint.astype('float32'), verbose=False).astype('int16')
# print(reduced_noise)

print(fint, len(fint), min(fint), max(fint))
print(reduced_noise, len(reduced_noise), min(reduced_noise), max(reduced_noise))

wf = wave.open('back.wav', 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(2)
wf.setframerate(RATE)
wf.writeframes(b''.join(fb))
wf.close()

wf = wave.open('filtered.wav', 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(2)
wf.setframerate(RATE)
wf.writeframes(reduced_noise.tobytes())
wf.close()

wf = wave.open('localrecord.wav', 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(2)
wf.setframerate(RATE)
wf.writeframes(b''.join(fm))
wf.close()

stream.stop_stream()
stream.close()
mic.terminate()

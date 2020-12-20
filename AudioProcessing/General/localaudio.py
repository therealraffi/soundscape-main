import pyaudio
import struct
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import math
import serial

s = serial.Serial(port='/dev/tty.usbserial-14230', baudrate=9600)
mic = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 8192
stream = mic.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                  input_device_index=3,
                  input=True, frames_per_buffer=CHUNK)

def sig(num):
    return 1/(1 + math.exp(-30 * num))

def get_rms(block):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack(format, block)

    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768.0)
        sum_squares += n**2
        
    # return 100 * (sum_squares/count) ** 0.5
    return int(2 * (100 * sig((sum_squares/count) ** 0.5) - 50))

while True:
    data = stream.read(CHUNK, exception_on_overflow=False)
    # print(get_rms(data))
    # print(data)
    amp = str(get_rms(data))
    out = "<%s, %s, %s, %s, %s, %s>" % (amp, amp, amp, amp, amp, amp)
    s.write(out.encode())
    data = np.frombuffer(data, dtype='b')
    volume_norm = int(np.linalg.norm(data)/100)
    print ("|" * int(amp))
    # print(volume_norm)

stream.stop_stream()
stream.close()
mic.terminate()

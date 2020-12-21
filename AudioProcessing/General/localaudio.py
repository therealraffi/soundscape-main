import pyaudio
import struct
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import wave
import math
import serial

#Arduino usb
s = serial.Serial(port='/dev/tty.usbserial-14230', baudrate=9600)
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

def sig(num):
    return 1/(1 + math.exp(-30 * num))

def amplitude(block):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack(format, block)

    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768.0)
        sum_squares += n**2
        
    # return 100 * (sum_squares/count) ** 0.5
    return int(2 * (100 * sig((sum_squares/count) ** 0.5) - 50))

def avgfreq(block):
        result = np.fromstring(block, dtype=np.int16)
        w = np.fft.fft(result)
        freqs = np.abs((np.fft.fftfreq(len(w))*44100))

        w = np.abs(w)
        indices = np.argsort(w)[int(len(w)*0.99):]
        bin_const = 10
        indices = indices[len(indices) % bin_const:]

        w = w[indices]
        freqs = freqs[indices]

        w = w[np.argsort(freqs)]
        freqs = np.sort(freqs)
        w = np.reshape(w, (-1, bin_const)).sum(axis=1)
        freqs = np.average(np.reshape(freqs, (-1, bin_const)), axis=1)
        w = w / np.sum(w)
        freqdict = dict(zip(freqs, w))

        out = 0
        for i in range(len(w)):
            out += w[i] * freqs[i]
        return int(out)

while True:
    data = stream.read(CHUNK, exception_on_overflow=False)

    #amplitude
    amp = str(amplitude(data))
    out = "<%s, %s, %s, %s, %s, %s>" % (amp, amp, amp, amp, amp, amp)
    #write command to ardunio
    s.write(out.encode())

    data = np.frombuffer(data, dtype='b')
    print(avgfreq(data), "\t", "|" * int(amp))

stream.stop_stream()
stream.close()
mic.terminate()

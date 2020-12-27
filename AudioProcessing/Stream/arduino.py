import socket
import threading
import pyaudio
import math
import struct
import wave
import numpy as np
import time
import serial

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def save(name, channels, rate, frames):
    wf = wave.open(name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def sig(num):
    return 1/(1 + math.exp(-20 * num))

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
        result = np.frombuffer(block, dtype=np.int16)
        w = np.fft.fft(result)
        freqs = np.abs((np.fft.fftfreq(len(w))*44100))
        w = np.abs(w)
        indices = np.argsort(w)[int(len(w)*0.99):]
        bin_const = 1
        indices = indices[len(indices) % bin_const:]
        w = w[indices]
        freqs = freqs[indices]
        w = w[np.argsort(freqs)]
        freqs = np.sort(freqs)
        w = np.reshape(w, (-1, bin_const)).sum(axis=1)
        freqs = np.average(np.reshape(freqs, (-1, bin_const)), axis=1)
        w = w / np.sum(w)
        
        freqdict = dict(zip(freqs, w))
        freqdict = {k:v for k, v in freqdict.items() if v * 100 > 1}
        
        wsum = sum(freqdict.values())
        wsum = wsum if wsum != 0 else 1

        '''
        print()
        for i in freqdict:
            print(int(i), "\t", freqdict[i] * 100 / wsum)
        print()
        '''

        out = 0
        for i in freqdict:
            out += i * freqdict[i] / wsum

        return None if math.isnan(float(out)) or len(freqdict) == 0 else max(1, int(out))

while True:
    try:
        #self.target_ip = input('Enter IP address of server --> ')
        #self.target_port = int(input('Enter target port of server --> '))
        target_ip = "173.66.155.183"
        target_port = 10000
        s.connect((target_ip, target_port))

        break
    except:
        print("Couldn't connect to server")

chunk_size = 8192 # 512
audio_format = pyaudio.paInt16
channels = 1
RATE = 44100
cRATE = 22050

print("Connected to Server")

fm, f0, f1, f2, f3 = [], [], [], [], []

print("Start Recording")

while True:
    try:
        data = s.recv(8192)

        channels = np.frombuffer(data, dtype='int16')
        c0 = channels[0::8] #red
        c1 = channels[1::8] #green
        c2 = channels[2::8] #blue
        c3 = channels[3::8] #purple

        fm.append(data)

        f0.append(c0.tobytes())
        f1.append(c1.tobytes())
        f2.append(c2.tobytes())
        f3.append(c3.tobytes())

        amp = amplitude(data)
        freq = avgfreq(data)

        #if freq != None:
#        print(freq, "|" * amp)
#        print(data)
#        print(f0[-1])
#        print("\n\n")

        print("%3s %6s \t %3s %6s \t %3s %6s \t %3s %6s" % (amplitude(f0[-1]), avgfreq(f0[-1]), amplitude(f1[-1]), avgfreq(f1[-1]), amplitude(f2[-1]), avgfreq(f2[-1]), amplitude(f3[-1]), avgfreq(f3[-1])), amp * "|")
    except KeyboardInterrupt as e:
        print("Client Disconnected")

        save("combined.wav", 4, RATE, fm)

        save("channel0.wav", 1, cRATE, f0)
        save("channel1.wav", 1, cRATE, f1)
        save("channel2.wav", 1, cRATE, f2)
        save("channel3.wav", 1, cRATE, f3)

        print("Done Saving")
        break

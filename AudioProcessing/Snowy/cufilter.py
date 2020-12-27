import socket
import threading
import pyaudio
import math
import struct
import wave
import numpy as np
import cupy as cp
import noisereduce as nr
import time
import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
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
        result = cp.array(result)
        w = cp.fft.fft(result)
        freqs = cp.abs((cp.fft.fftfreq(len(w))*44100))
        w = cp.abs(w)
        indices = cp.argsort(w)[int(len(w)*0.99):]
        bin_const = 1
        indices = indices[len(indices) % bin_const:]
        w = w[indices]
        freqs = freqs[indices]
        w = w[cp.argsort(freqs)]
        freqs = cp.sort(freqs)
        w = cp.reshape(w, (-1, bin_const)).sum(axis=1)
        freqs = cp.average(cp.reshape(freqs, (-1, bin_const)), axis=1)
        w = w / cp.sum(w)
        
        freqdict = dict(zip(freqs.get(), w.get()))
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

def filter(audio, background):
    reduced_noise = nr.reduce_noise(audio_clip=audio.astype('float32'), noise_clip=background.astype('float32'), verbose=False).astype('int16')
    return reduced_noise.tobytes()

while True:
    try:
        target_ip = "173.66.155.183"
        target_port = 10000
        s.connect((target_ip, target_port))

        break
    except:
        print("Couldn't connect to server")

chunk_size = 8192 
audio_format = pyaudio.paInt16
RATE = 44100
cRATE = 22050

print("Connected to Server")

fm, f0, f1, f2, f3 = [], [], [], [], []

print("Start Background Recording")

t1 = time.time()
backint = np.array([], dtype=np.int16)
fb = []
while(time.time() - t1 < 2):
    data = s.recv(8192)
    fb.append(data)

    data = np.frombuffer(data, dtype=np.int16)
    backint = np.append(backint, data)

print("Start Main Stream")

filtered = []

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

        if freq != None:
            print(freq, "|" * amp)
        
        t1 = time.time()
        print(amplitude(f0[-1]), avgfreq(f0[-1]), "\t", amplitude(f1[-1]), avgfreq(f1[-1]), "\t", amplitude(f2[-1]), avgfreq(f2[-1]), "\t", amplitude(f3[-1]), avgfreq(f3[-1]))        
        print(time.time() - t1)
        filterout = filter(channels, backint)
        filtered.append(filterout)

        #amp2 = amplitude(filterout)
        #print(amp, amp2, freq, avgfreq(filterout))

    except KeyboardInterrupt as e:
        print("Client Disconnected")

        save("back.wav", 4, RATE, fb)
        save("filtered.wav", 4, RATE, filtered)
        save("combined.wav", 4, RATE, fm)

        save("channel0.wav", 1, cRATE, f0)
        save("channel1.wav", 1, cRATE, f1)
        save("channel2.wav", 1, cRATE, f2)
        save("channel3.wav", 1, cRATE, f3)

        print("Done Saving")

        break

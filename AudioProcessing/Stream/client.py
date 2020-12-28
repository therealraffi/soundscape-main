import socket
import threading
import pyaudio
import math
import struct
import wave
import numpy as np

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while True:
    target_ip = "127.0.0.1"
    target_port = 5500
    s.connect((target_ip, target_port))

def save(name, channels, rate, frames):
    wf = wave.open(name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def receive_server_data():
    while True:
        try:
            data = s.recv(8192)
        except:
            pass
        
chunk_size = 8192 # 512
audio_format = pyaudio.paInt16
channels = 1
RATE = 44100
cRATE = 22050

print("Connected to Server")

fm, f0, f1, f2, f3 = [], [], [], [], []

while True:
    try:
        data = s.recv(8192)
        print(data)
    
        channels = np.frombuffer(data, dtype='int16')
        # c0 = channels[0::8] #red
        # c1 = channels[1::8] #green
        # c2 = channels[2::8] #blue
        # c3 = channels[3::8] #purple

        fm.append(data)
        # f0.append(c0.tobytes())
        # f1.append(c1.tobytes())
        # f2.append(c2.tobytes())
        # f3.append(c3.tobytes())

        # f3[-1]

    except KeyboardInterrupt as e:
        print("Client Disconnected")

        save("combined.wav", 1, RATE, fm)

        # save("channel0.wav", 1, cRATE, f0)
        # save("channel1.wav", 1, cRATE, f1)
        # save("channel2.wav", 1, cRATE, f2)
        # save("channel3.wav", 1, cRATE, f3)

        print("Done Saving")
        break
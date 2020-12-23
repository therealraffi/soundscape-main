import socket
import threading
import pyaudio
import math
import struct
import wave
import numpy as np

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

def receive_server_data():
    while True:
        try:
            data = s.recv(8192)
            playing_stream.write(data)
        except:
            pass
        
chunk_size = 8192 # 512
audio_format = pyaudio.paInt16
channels = 1
RATE = 44100
cRATE = 22050

# initialise microphone recording
p = pyaudio.PyAudio()
# playing_stream = p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size)

print("Connected to Server")

# start threads
# receive_thread = threading.Thread(target=receive_server_data).start()

fm, f0, f1, f2, f3 = [], [], [], [], []
while True:
    try:
        data = s.recv(8192)
        # playing_stream.write(data)
    
        channels = np.fromstring(data, dtype='int16')
        c0 = channels[0::8] #red
        c1 = channels[1::8] #green
        c2 = channels[2::8] #blue
        c3 = channels[3::8] #purple

        fm.append(data)
        f0.append(c0.tostring())
        f1.append(c1.tostring())
        f2.append(c2.tostring())
        f3.append(c3.tostring())

    except KeyboardInterrupt as e:
        print("Client Disconnected")

        wf = wave.open('combined.wav', 'wb')
        wf.setnchannels(4)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b''.join(fm))
        wf.close()

        wf = wave.open('channel0.wav', 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(cRATE)
        wf.writeframes(b''.join(f0))
        wf.close()

        wf1 = wave.open('channel1.wav', 'wb')
        wf1.setnchannels(1)
        wf1.setsampwidth(2)
        wf1.setframerate(cRATE)
        wf1.writeframes(b''.join(f1))
        wf1.close()

        wf2 = wave.open('channel2.wav', 'wb')
        wf2.setnchannels(1)
        wf2.setsampwidth(2)
        wf2.setframerate(cRATE)
        wf2.writeframes(b''.join(f2))
        wf2.close()

        wf3 = wave.open('channel3.wav', 'wb')
        wf3.setnchannels(1)
        wf3.setsampwidth(2)
        wf3.setframerate(cRATE)
        wf3.writeframes(b''.join(f3))
        wf3.close()
        print("done saving")
        stream = False
        break
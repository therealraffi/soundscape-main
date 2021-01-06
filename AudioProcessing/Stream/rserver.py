import socket
import threading
import pyaudio
import wave
import numpy as np
import struct

ip = socket.gethostbyname(socket.gethostname())

mic = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 8192//2
RECORD_SECONDS = 1.5

stream = mic.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                  input_device_index=2,
                  input=True, frames_per_buffer=CHUNK)

fm = []

while True:
    try:
        port = 5500
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        break
    except Exception as e:
        print(e)
        exit()

def save(name, channels, rate, frames):
    wf = wave.open(name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()


def accept_connections():
    s.listen()
    print('Running on IP: '+ip)
    print('Running on port: '+str(port))

    while True:
        try:
            c, addr = s.accept()
            connections.append(c)
            threading.Thread(target=handle_client,args=(c,addr)).start()
        except KeyboardInterrupt as e:
            print(e)
            save("server-combined.wav", 1, RATE, fm)
            print('Saved')
            c.close()
            exit(0)       

def broadcast(sock, data):
    for client in connections:
        if client != s and client != sock:
            try:
                client.send(data)
            except:
                pass
def handle_client(c, addr):
    print("Start")
    global fm
    while True:
        try:
            # frames = np.array([])
            # data = 0
            # for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            #     data = stream.read(CHUNK, exception_on_overflow=False)
            #     frames = np.append(frames, np.fromstring(data, dtype=np.float32))
            # print(len(frames))

            # scalar = np.full(1, 128)
            data = stream.read(CHUNK, exception_on_overflow=False)
            # d = np.array(struct.unpack(str(2*CHUNK) + 'B', data), dtype='b')[::2]
            # da = np.add(d, scalar)

            print(len(data))
            fm.append(data)
            broadcast(c, data)     

        except Exception as e:
            print(e)
            c.close()
            exit()
            

connections = []
accept_connections()


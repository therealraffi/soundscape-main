import socket
import threading
import pyaudio
import wave
import numpy as np

ip = socket.gethostbyname(socket.gethostname())

mic = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 8192
stream = mic.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                  input_device_index=2,
                  input=True, frames_per_buffer=CHUNK)

global fm 
fm = []

while True:
    try:
        port = 5500
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((ip, port))
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
            threading.Thread(target=handle_client,args=(c,addr,)).start()
        except KeyboardInterrupt as e:
            save("server-combined.wav", 1, RATE, fm)
            exit()

def broadcast(sock, data):
    for client in connections:
        if client != s and client != sock:
            try:
                client.send(data)
            except:
                pass

def handle_client(c, addr):
    print("Start")
    while True:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            fm.append(data)
            broadcast(c, data)

        except socket.error:
            c.close()

connections = []
accept_connections()
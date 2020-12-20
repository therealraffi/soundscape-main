import socket
import pyaudio
import numpy as np

# Socket
HOST = "192.168.1.218"
PORT = 10000

# Audio
p = pyaudio.PyAudio()
CHUNK = 1024 * 4
FORMAT = pyaudio.paInt32
CHANNELS = 2
RATE = 44100
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK)

with socket.socket() as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    conn, address = server_socket.accept()
    print("Connection from " + address[0] + ":" + str(address[1]))

    data = conn.recv(8192)
    while data != "":
        try:
            data = conn.recv(8192)
            stream.write(data)
        except socket.error:
            print("Client Disconnected")
            break

stream.stop_stream()
stream.close()
p.terminate()
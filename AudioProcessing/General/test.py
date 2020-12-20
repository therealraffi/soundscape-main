import socket
import pyaudio

# Socket
HOST = "192.168.1.218"
PORT = 10000

# Audio
p = pyaudio.PyAudio()

for i in range(10):
    print(p.get_device_info_by_index(i)["maxInputChannels"])
    print("\n")
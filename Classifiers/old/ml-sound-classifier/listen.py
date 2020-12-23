import socket
import pyaudio
import numpy as np
import wave
# Socket
HOST = "192.168.1.218"
PORT = 10000

# Audio
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (HOST, PORT)
sock.bind(server_address)
sock.listen(1)

CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 4
RATE = 44100
cRATE = 22050

#record channel
fm, f0, f1, f2, f3 = [], [], [], [], []
stream = True

while stream:
    connection, client_address = sock.accept()
    data = connection.recv(8192)

    while data != "":
        try:
            data = connection.recv(8192)
            # print(np.sqrt(np.mean(data**2)))
            # print("\n\n\n", abs(data[0]), data[0], "\n", data, "\n\n\n")
            channels = np.fromstring(data, dtype='int16')
            c0 = channels[0::8] #red
            c1 = channels[1::8] #green
            c2 = channels[2::8] #blue
            c3 = channels[3::8] #purple

            print(np.sqrt(np.mean(c0**2)), np.sqrt(np.mean(c1**2)), np.sqrt(np.mean(c2**2)), np.sqrt(np.mean(c3**2)))

            fm.append(data)
            f0.append(c0.tostring())
            f1.append(c1.tostring())
            f2.append(c2.tostring())
            f3.append(c3.tostring())

        except (socket.error, KeyboardInterrupt) as e:
            print("Client Disconnected")

            wf = wave.open('class.wav', 'wb')
            wf.setnchannels(4)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b''.join(fm))
            wf.close()

            wf = wave.open('out0.wav', 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cRATE)
            wf.writeframes(b''.join(f0))
            wf.close()

            wf1 = wave.open('out1.wav', 'wb')
            wf1.setnchannels(1)
            wf1.setsampwidth(2)
            wf1.setframerate(cRATE)
            wf1.writeframes(b''.join(f1))
            wf1.close()

            wf2 = wave.open('out2.wav', 'wb')
            wf2.setnchannels(1)
            wf2.setsampwidth(2)
            wf2.setframerate(cRATE)
            wf2.writeframes(b''.join(f2))
            wf2.close()

            wf3 = wave.open('out3.wav', 'wb')
            wf3.setnchannels(1)
            wf3.setsampwidth(2)
            wf3.setframerate(cRATE)
            wf3.writeframes(b''.join(f3))
            wf3.close()
            print("done saving")
            stream = False
            break
        
import socket
import pyaudio
import numpy as np
import wave
# Socket
HOST = "192.168.1.218"
PORT = 10000

# Audio
p = pyaudio.PyAudio()
CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 4
RATE = 44100
cRATE = 22050
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK)

channel0 = p.open(format=FORMAT,
                channels=1,
                rate=cRATE,
                output=True,
                frames_per_buffer=1024)

#record channel
fm, f0, f1, f2, f3 = [], [], [], [], []

with socket.socket() as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    conn, address = server_socket.accept()
    print("Connection from " + address[0] + ":" + str(address[1]))

    data = conn.recv(8192)
    while data != "":
        try:
            data = conn.recv(8192)
            channels = np.fromstring(data, dtype='int16')
            c0 = channels[0::8]
            c1 = channels[1::8]
            c2 = channels[2::8]
            c3 = channels[3::8]

            fm.append(data)
            f0.append(c0.tostring())
            f1.append(c1.tostring())
            f2.append(c2.tostring())
            f3.append(c3.tostring())
            # print(channels)
            # print(c0)
            # print(c1)
            # print("\n\n\n")
            stream.write(data)
            # channel0.write(c0.tostring())
        except (socket.error, KeyboardInterrupt) as e:
            print("Client Disconnected")

            stream.stop_stream()
            stream.close()
            p.terminate()

            wf = wave.open('class.wav', 'wb')
            wf.setnchannels(4)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(fm))
            wf.close()

            wf = wave.open('out0.wav', 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(cRATE)
            wf.writeframes(b''.join(f0))
            wf.close()

            wf1 = wave.open('out1.wav', 'wb')
            wf1.setnchannels(1)
            wf1.setsampwidth(p.get_sample_size(FORMAT))
            wf1.setframerate(cRATE)
            wf1.writeframes(b''.join(f1))
            wf1.close()

            wf2 = wave.open('out2.wav', 'wb')
            wf2.setnchannels(1)
            wf2.setsampwidth(p.get_sample_size(FORMAT))
            wf2.setframerate(cRATE)
            wf2.writeframes(b''.join(f2))
            wf2.close()

            wf3 = wave.open('out3.wav', 'wb')
            wf3.setnchannels(1)
            wf3.setsampwidth(p.get_sample_size(FORMAT))
            wf3.setframerate(cRATE)
            wf3.writeframes(b''.join(f3))
            wf3.close()
            break
        
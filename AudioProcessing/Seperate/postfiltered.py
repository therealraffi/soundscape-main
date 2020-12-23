import socket
import pyaudio
import numpy as np
import wave
import math
import struct

# Socket
HOST = "192.168.1.218"
PORT = 10010

# Audio
p = pyaudio.PyAudio()
CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 4
RATE = 44100
cRATE = 22050

#record channel
fm, f0, f1, f2, f3 = [], [], [], [], []

def sig(num):
    return 1/(1 + math.exp(-10 * num))

def amplitude(block):
    count = len(block)/2
    count = count if count != 0 else 1
    format = "%dh"%(count)
    shorts = struct.unpack(format, block)

    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768.0)
        sum_squares += n**2
        
    # return 100 * (sum_squares/count) ** 0.5
    return int(2 * (100 * sig((sum_squares/count) ** 0.5) - 50))

def avgfreq(block):
        result = np.fromstring(block, dtype=np.int16)
        w = np.fft.fft(result)
        freqs = np.abs((np.fft.fftfreq(len(w))*44100))
        w = np.abs(w)
        indices = np.argsort(w)[int(len(w)*0.99):]
        print(indices)
        bin_const = 10
        indices = indices[len(indices) % bin_const:]
        w = w[indices]
        freqs = freqs[indices]
        w = w[np.argsort(freqs)]
        freqs = np.sort(freqs)
        w = np.reshape(w, (-1, bin_const)).sum(axis=1)

        if len(freqs) == 0:
            return None

        freqs = np.average(np.reshape(freqs, (-1, bin_const)), axis=1)
        w = w / np.sum(w)
        freqdict = dict(zip(freqs, w))
        wsum = sum(w)
        wsum = wsum if wsum != 0 else 1
        out = 0
        for i in range(len(w)):
            out += w[i] * freqs[i] / wsum
        return 0 if math.isnan(float(out)) else int(out)

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

            print(amplitude(f0[-1]), avgfreq(f0[-1]), "\t", amplitude(f1[-1]), avgfreq(f1[-1]), "\t", amplitude(f2[-1]), avgfreq(f2[-1]), "\t", amplitude(f3[-1]), avgfreq(f3[-1]))
        except (socket.error, KeyboardInterrupt) as e:
            print("Client Disconnected")
            p.terminate()

            wf = wave.open('combinedpost.wav', 'wb')
            wf.setnchannels(4)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(fm))
            wf.close()

            wf = wave.open('post0.wav', 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(cRATE)
            wf.writeframes(b''.join(f0))
            wf.close()

            wf1 = wave.open('post1.wav', 'wb')
            wf1.setnchannels(1)
            wf1.setsampwidth(p.get_sample_size(FORMAT))
            wf1.setframerate(cRATE)
            wf1.writeframes(b''.join(f1))
            wf1.close()

            wf2 = wave.open('post2.wav', 'wb')
            wf2.setnchannels(1)
            wf2.setsampwidth(p.get_sample_size(FORMAT))
            wf2.setframerate(cRATE)
            wf2.writeframes(b''.join(f2))
            wf2.close()

            wf3 = wave.open('post3.wav', 'wb')
            wf3.setnchannels(1)
            wf3.setsampwidth(p.get_sample_size(FORMAT))
            wf3.setframerate(cRATE)
            wf3.writeframes(b''.join(f3))
            wf3.close()
            break
        
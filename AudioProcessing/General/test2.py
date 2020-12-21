import sys
import json
import pyaudio
import numpy as np
import matplotlib.pyplot as plt

CHUNKSIZE = 1024*2  # fixed chunk size

# initialize portaudio

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                  input_device_index=6,
                input=True, frames_per_buffer=CHUNKSIZE)

# Wait to start recording

result = np.array([], dtype=np.int16)

try:

    print("Press [Ctrl] + [C] to stop recording")

    while True:

        # Get the last two chunks into numpydata

        data = stream.read(CHUNKSIZE)
        newdata = np.fromstring(data, dtype=np.int16)
        result = np.append(result, newdata)

except KeyboardInterrupt:
    pass

print("Cleaning up...")

# Cleanup

stream.stop_stream()
stream.close()
p.terminate()

print("Parsing frequencies")

w = np.fft.fft(result)
freqs = np.abs((np.fft.fftfreq(len(w))*44100))

w = np.abs(w)

indices = np.argsort(w)[int(len(w)*0.99):]

bin_const = 10
indices = indices[len(indices) % bin_const:]

w = w[indices]
freqs = freqs[indices]

w = w[np.argsort(freqs)]
freqs = np.sort(freqs)

w = np.reshape(w, (-1, bin_const)).sum(axis=1)
freqs = np.average(np.reshape(freqs, (-1, bin_const)), axis=1)

w = w / np.sum(w)

freqdict = dict(zip(freqs, w))

data = json.dumps(freqdict)

# print(data)

plt.plot(freqs, w, zorder=-1)

#min
plt.plot(freqs, np.array([np.min(w)*2]*len(freqs)))

result = []

insidePeak = False

t = np.min(w)*3

row = []

wsum = sum(w)

for i in freqdict:
    print(int(i), "\t", freqdict[i] * 100 / wsum)

for height, freq in zip(w, freqs):

    if freq < 100:
        continue

    if height > t:
        insidePeak = True
    else:
        if insidePeak:
            result.append(sorted(row)[-1])
            row = []
        insidePeak = False

    if insidePeak:
        row.append((height, freq))


plt.scatter(np.array([x[1] for x in result]), np.array([x[0] for x in result]))

mul = 1/np.sum(np.array([x[0] for x in result]))

resarr = []

for x in result:
    resarr.append({"Freq": x[1], "Volume": mul*x[0]})
    # print("========================")
    #print("Frequency: "+str(x[1]))
    #print("Volume: "+str(mul*x[0]))
    # print("========================")

plt.show()


if len(sys.argv[0]) > 1:
    with open(sys.argv[1], "w") as f:
        f.write(json.dumps(resarr))

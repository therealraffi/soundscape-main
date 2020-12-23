
import pyaudio
import numpy as np
import wave
import struct
import matplotlib.pyplot as plt
import matplotlib.animation
import time

RATE = 16000
CHUNK  = 2048 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# create matplotlib figure and axes
plt.ion()
fig, ax = plt.subplots(1, figsize=(15, 7))

# pyaudio class instance
p = pyaudio.PyAudio()
print(p.get_default_input_device_info())

# stream object to get data from microphone
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

# variable for plotting
x = np.arange(0, 2 * CHUNK, 2)

# create a line object with random data
line, = ax.plot(x, np.random.rand(CHUNK), '-', lw=2)

# basic formatting for the axes
ax.set_title('AUDIO WAVEFORM')
ax.set_xlabel('samples')
ax.set_ylabel('volume')
ax.set_ylim(0, 255)
ax.set_xlim(0, 2 * CHUNK)
plt.setp(ax, xticks=[0, CHUNK, 2 * CHUNK], yticks=[0, 128, 255])

# show the plot

print('stream started')

# for measuring frame rate
frame_count = 0
start_time = time.time()


# show the plot
# plt.show(block=False)

# update figure canvas
print(time.time() - start_time)
while(time.time() - start_time < 10):
    # binary data
    print(time.time() - start_time)
    data = stream.read(CHUNK, exception_on_overflow=False)  

    # convert data to integers, make np array, then offset it by 127
    data_int = struct.unpack(str(2 * CHUNK) + 'B', data)

    # create np array and offset by 128
    data_np = np.array(data_int, dtype='b')[::2] + 128

    line.set_ydata(data_np)
    try:
        fig.canvas.draw()
        fig.canvas.flush_events()
        frame_count += 1
        
    except Exception as e:
        
        # calculate average frame rate
        frame_rate = frame_count / (time.time() - start_time)
        
        print('stream stopped')
        print('average frame rate = {:.0f} FPS'.format(frame_rate))

stream.stop_stream()
stream.close()
p.terminate()

import librosa
import numpy as np
import noisereduce as nr
from tensorflow import keras
from keras.layers import Dense, Dropout, Activation, Flatten,LSTM,TimeDistributed
from keras.optimizers import Adam,SGD

# Load audio file
audio_data, sampling_rate = librosa.load('applause3.wav')
# Noise reduction
noisy_part = audio_data[0:25000]  
reduced_noise = nr.reduce_noise(audio_clip=audio_data, noise_clip=noisy_part, verbose=False)
# Visualize
print("Original audio file:")
print("Noise removed audio file:")


trimmed, index = librosa.effects.trim(reduced_noise, top_db=20, frame_length=512, hop_length=64)
print("Trimmed audio file:")

stft = np.abs(librosa.stft(trimmed, n_fft=512, hop_length=256, win_length=512))

model = keras.Sequential()
model.add(Dense(256, input_shape=(257,)))
model.add(Activation("relu"))

model.add(Dense(256))
model.add(Activation("relu"))

model.add(Dense(128))
model.add(Activation("relu"))

model.add(Dense(128))
model.add(Activation("relu"))
model.add(Dropout(0.5))
model.add(Dense(num_labels))
model.add(Activation(‘relu’))
model.compile(loss=’categorical_crossentropy’, metrics=[‘accuracy’], optimizer=’adam’)
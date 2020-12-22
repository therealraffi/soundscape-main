import noisereduce as nr
from scipy.io import wavfile
import librosa
# load data
rate, data = wavfile.read("localrecord.wav")
print(rate)
noisy_part = data[100:1500]
print(len(data), data.shape)

reduced_noise = nr.reduce_noise(audio_clip=data.astype('float32'), noise_clip=noisy_part.astype('float32'), verbose=True)

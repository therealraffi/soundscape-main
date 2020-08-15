import librosa
import numpy as np
import noisereduce as nr

# Load audio file
audio_data, sampling_rate = librosa.load(<audio_file_path.wav>)
# Noise reduction
noisy_part = audio_data[0:25000]  
reduced_noise = nr.reduce_noise(audio_clip=audio_data, noise_clip=noisy_part, verbose=False)
# Visualize
print("Original audio file:")
plotAudio(audio_data)
print("Noise removed audio file:")
plotAudio(reduced_noise)


trimmed, index = librosa.effects.trim(reduced_noise, top_db=20, frame_length=512, hop_length=64)
print("Trimmed audio file:")
plotAudio(trimmed)

stft = np.abs(librosa.stft(trimmed, n_fft=512, hop_length=256, win_length=512))
import pandas as pd
import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
#from tqdm import tqdm_notebook as tqdm
from tqdm import tqdm
import os
from torchvision.models import resnet34
import pickle


def spec_to_image(spec, eps=1e-6):
    mean = spec.mean()
    std = spec.std()
    spec_norm = (spec - mean) / (std + eps)
    spec_min, spec_max = spec_norm.min(), spec_norm.max()
    spec_scaled = 255 * (spec_norm - spec_min) / (spec_max - spec_min)
    spec_scaled = spec_scaled.astype(np.uint8)
    return spec_scaled


def get_melspectrogram_db(wav, sr, n_fft=2048, hop_length=512, n_mels=128, fmin=20, fmax=8300, top_db=80):
    #wav,sr = librosa.load(file_path,sr=sr)
    if wav.shape[0]<5*sr:
        wav=np.pad(wav,int(np.ceil((5*sr-wav.shape[0])/2)),mode='reflect')
    else:
        wav=wav[:5*sr]
    spec=librosa.feature.melspectrogram(wav, sr=sr, n_fft=n_fft, hop_length=hop_length,n_mels=n_mels,fmin=fmin,fmax=fmax)
    spec_db=librosa.power_to_db(spec,top_db=top_db)
    return spec_db

def predict(model, device, classes, clip, sr):

    with open('indtocat.pkl','rb') as f:
        indtocat = pickle.load(f)
    spec=spec_to_image(get_melspectrogram_db(clip, sr))
    spec_t=torch.tensor(spec).to(device, dtype=torch.float32)
    pr=model.forward(spec_t.reshape(1,1,*spec_t.shape))
    ind = pr.argmax(dim=1).cpu().detach().numpy().ravel()[0]

    return indtocat[ind]

CLASS_PATH = '../ESC-classes.txt'
WEIGHT_PATH = 'esc50resnet.pth'
SAMPLE_RATE = 44100
filename = "baby_cry.wav"
GPU = "2"

print("Preprocessing...")

device = torch.device("cuda:"+GPU if torch.cuda.is_available() else "cpu")
print(device)
#model = torch.load(WEIGHT_PATH, volatile=True)

#model =  resnet34(pretrained=True)
#model.fc = nn.Linear(512,50)
#model.conv1 = nn.Conv2d(1, 64, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3), bias=False)
#model = model.to(device)
weights = torch.load(WEIGHT_PATH, map_location='cpu')
#print(weights)
model = weights.to(device)
model.eval()
#model.load_stae_dict(weights)

classes=[]
for c in open(CLASS_PATH, 'r'):
        classes.append(c)

clip,sr = librosa.load(filename,sr=SAMPLE_RATE)

print("Started")

print("Predicted:", predict(model, device, classes, clip, SAMPLE_RATE))

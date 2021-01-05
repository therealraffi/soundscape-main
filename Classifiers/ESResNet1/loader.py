import io
import os
import glob
import json
import time
import tqdm
import signal
import argparse
import numpy as np
from PIL import Image

import torch
import torch.utils.data
import torch.nn.functional as F

import torchaudio
import torchvision

import ignite.engine as ieng
import ignite.metrics as imet
import ignite.handlers as ihan

from model import esresnet

import os
import warnings
import multiprocessing as mp

import numpy as np
import pandas as pd
import sklearn.model_selection as skms
import scipy.signal as sps

import tqdm
import librosa

import torch.utils.data as td

from utils import transforms

from typing import Tuple
from typing import Optional

def scale(old_value, old_min, old_max, new_min, new_max):
    old_range = (old_max - old_min)
    new_range = (new_max - new_min)
    new_value = (((old_value - old_min) * new_range) / old_range) + new_min

    return new_value

def process(wav, sr, args):
    wav, sample_rate = librosa.load(filename, sr=sr, mono=True)
    if wav.ndim == 1:
        wav = wav[:, np.newaxis]

    if np.abs(wav.max()) > 1.0:
        wav = scale(wav, wav.min(), wav.max(), -1.0, 1.0)

    wav = wav.T * 32768.0
    wav = wav.astype(np.float32)
    
    x = torch.Tensor(wav)

    window_buffer: torch.Tensor = torch.from_numpy(
        sps.get_window(window=args["window"], Nx=args["win_length"], fftbins=True)
    ).to(torch.get_default_dtype())
    window = window_buffer

    spec = torch.stft(
            x.view(-1, x.shape[-1]),
            n_fft=args["n_fft"],
            hop_length=args["hop_length"],
            win_length=args["win_length"],
            window=window,
            pad_mode='reflect',
            normalized=args["normalized"],
            onesided=True
    )

    if not args["onesided"]:
        spec = torch.cat((torch.flip(spec, dims=(-3,)), spec), dim=-3)

    spec_height_3_bands = spec.shape[-3] // 3
    spec_height_single_band = 3 * spec_height_3_bands
    spec = spec[:, :spec_height_single_band]

    spec = spec.reshape(x.shape[0], -1, spec.shape[-3] // 3, *spec.shape[-2:])

    spec_height = spec.shape[-3] if args["spec_height"] < 1 else args["spec_height"]
    spec_width = spec.shape[-2] if args["spec_width"] < 1 else args["spec_width"]

    pow_spec = spec[..., 0] ** 2 + spec[..., 1] ** 2

    if spec_height != pow_spec.shape[-2] or spec_width != pow_spec.shape[-1]:
        pow_spec = F.interpolate(
            pow_spec,
            size=(spec_height, spec_width),
            mode='bilinear',
            align_corners=True
        )

    log10_eps = 1e-18
    pow_spec = torch.where(pow_spec > 0.0, pow_spec, torch.full_like(pow_spec, log10_eps))

    pow_spec = pow_spec.view(x.shape[0], -1, 3, *pow_spec.shape[-2:])

    return pow_spec

def process2(clip, sr):
    num_channels = 3
    window_sizes = [25, 50, 100]
    hop_sizes = [10, 25, 50]
    centre_sec = 2.5
    specs = []

    for i in range(num_channels):
        window_length = int(round(window_sizes[i]*SAMPLE_RATE/1000))
        hop_length = int(round(hop_sizes[i]*SAMPLE_RATE/1000))

        clip = torch.Tensor(clip)
        spec = torchaudio.transforms.MelSpectrogram(SAMPLE_RATE, n_fft=4410, win_length=window_length, hop_length=hop_length, n_mels=128)(clip)
		#print(spec.shape)
        eps = 1e-6
        spec = spec.numpy()
        spec = np.log(spec+ eps)
        spec = np.asarray(torchvision.transforms.Resize((128, 250))(Image.fromarray(spec)))
        specs.append(spec)

    specs = np.array(specs)
    values = torch.Tensor(specs)
    values = values.reshape(1, 3, 128, 250)

    return values

args = {
      "n_fft": 2048,
      "hop_length": 561,
      "win_length": 1654,
      "window": "blackmanharris",
      "normalized": True,
      "onesided": True,
      "spec_height": -1,
      "spec_width": -1,
      "num_classes": 50,
      "pretrained": True,
      "lock_pretrained": False
    }

filename = 'baby_cry.wav'
SAMPLE_RATE = 44100
MODEL_PATH = "~/saved_models/ESC50_STFT_ESRN-CV1/'ESC50_STFT_ESRN-CV1_ESRN-CV1_performance=0.5725.pth'"
MODEL_PATH = 'best.pth'
CLASS_PATH = '../ESC-classes.txt'
GPU = "1"

model = esresnet.ESResNet(**args)
print([i for i in torch.load(MODEL_PATH)])
model.load_state_dict(torch.load(MODEL_PATH))
model.eval()
##print(model)

device = torch.device("cuda:"+GPU if torch.cuda.is_available() else "cpu")
#device="cpu"

classes = []
for c in open(CLASS_PATH, 'r'):
        classes.append(c)

wav, sample_rate = librosa.load(filename, sr=SAMPLE_RATE, mono=True)
inputs = process(wav, sample_rate, args).to(device)
print(inputs)
outputs = model(inputs)
_, predicted = torch.max(outputs.data, 1)
pred = classes[predicted[0]].replace('\n', '')

print(pred)

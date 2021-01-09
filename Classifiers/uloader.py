from argparse import ArgumentParser
import os

# FILTER WARNINGS
from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter("ignore", category=NumbaDeprecationWarning)
warnings.simplefilter("ignore", category=NumbaPendingDeprecationWarning)

import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.nn import BCELoss
from torch.optim import Adam
from optimizer.lookahead import Lookahead
from optimizer.ralamb import Ralamb

from pytorch_lightning.core.lightning import LightningModule
from pytorch_lightning import Trainer, seed_everything, loggers
from pytorch_lightning.callbacks import EarlyStopping, ModelCheckpoint
from pytorch_lightning import loggers as pl_loggers

from albumentations import Compose, ShiftScaleRotate, GridDistortion, Cutout

from utils.metrics import accuracy, compute_macro_auprc, compute_micro_auprc, compute_micro_F1, mean_average_precision

import pandas as pd
from prepare_data.urbansound8k import UrbanSound8K_TALNet
from prepare_data.esc50 import ESC50_TALNet
from prepare_data.sonycust import SONYCUST_TALNet
from models.TALNet import TALNetV3NoMeta
from losses.DCASEmaskedLoss import *
import config
import librosa
import torchaudio
from models.panns import Cnn10, Mixup, do_mixup

from model_TALNetV3_training import TALNetV3Classifier
from model_CNN10TL_training import CNN10Classifier

def predict_cnn(wav, sr, model, device, m, classes):
    melspec = librosa.feature.melspectrogram(
        wav, sr=44100, n_fft=2822, hop_length=1103, n_mels=64, fmin=0, fmax=8000
    )
    logmel = librosa.core.power_to_db(melspec).transpose()
    logmel = np.expand_dims(logmel, axis=0)
    inputs = torch.Tensor(logmel).float()
    inputs = inputs.to(device)
    lambdas = torch.FloatTensor(m.get_lambda(batch_size=1)).to(device)
    outputs = model(inputs, lambdas)
    _, predicted = torch.max(outputs.data, 1)
    pred = [classes[i].replace('\n', '') for i in predicted]
    return pred

def predict_talnet(wav, sr, model, device, classes):
    melspec = librosa.feature.melspectrogram(
        wav, sr=44100, n_fft=2822, hop_length=1103, n_mels=64, fmin=0, fmax=8000
    )
    logmel = librosa.core.power_to_db(melspec).transpose()
    logmel = np.expand_dims(logmel, axis=0)
    inputs = torch.Tensor(logmel).float()
    inputs = inputs.to(device)
    outputs = model(inputs)[0]
    _, predicted = torch.max(outputs.data, 1)
    pred = [classes[i].replace('\n', '') for i in predicted]
    return pred

CLASS_PATH = '../ESC-classes.txt'
TALNET_PATH = 'checks/TALNetV3/TALNetV3-epoch148.ckpt'
CNN_PATH = "checks/CNN10TL/CNN10TL-epoch306.ckpt"

CNN_HPARAMS = "../data/summaries/CNN10TLAllDatasets/logs/default/version_14/hparams.yaml"
TALNET_HPARAMS = "../data/summaries/TALNetV3AllDatasets/logs/default/version_9/hparams.yaml"

SAMPLE_RATE = 44100
filename = "baby_cry.wav"
GPU = "1"

print("Preprocessing...")

cparams = {}
tparams = {}
for line in open(CNN_HPARAMS, 'r').read().splitlines():
    k, v = line.split(": ")
    cparams[k] = v
for line in open(TALNET_HPARAMS, 'r').read().splitlines():
    k, v = line.split(": ")
    tparams[k] = v

device = torch.device("cuda:"+GPU if torch.cuda.is_available() else "cpu")

clip, sr = librosa.load(filename, SAMPLE_RATE)
#clip, sr = torchaudio.load(filename)

mixup_augmenter = Mixup(float(cparams["alpha"]), int(cparams["seed"]))

modelc = CNN10Classifier.load_from_checkpoint(
    CNN_PATH, 
    hparams=cparams,
    fold=1
)
modelc = modelc.to(device)
modelc.eval()

modelt = TALNetV3Classifier.load_from_checkpoint(TALNET_PATH, hparams=tparams, fold=1)
modelt = modelt.to(device)
modelt.eval()

classes=[]
for c in open(CLASS_PATH, 'r').read().splitlines():
        classes.append(c)

print("Started")
print("Predicted TALNET:", predict_talnet(clip, sr, modelt, device, classes))
print("Predicted CNN:", predict_cnn(clip, sr, modelc, device, mixup_augmenter, classes))

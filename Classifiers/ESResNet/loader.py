import io
import os
import glob
import json
import time
import tqdm
import signal
import argparse
import numpy as np

import torch
import torch.utils.data
import torch.nn.functional

import torchvision as tv

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

import tqdm
import librosa

import torch.utils.data as td

from utils import transforms

from typing import Tuple
from typing import Optional

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

model = esresnet.ESResNet(**args)
model.load_state_dict(torch.load("highest.pth"))
model.eval()
##print(model)

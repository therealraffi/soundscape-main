#ac
import torch
import torchvision
import torch.nn as nn
import numpy as np
import json
import utils
import validate #Directory
import argparse
import models.densenet
import models.resnet
import models.inception #Directory
import time
import dataloaders.datasetaug #Directory
import dataloaders.datasetnormal
import torchaudio
import librosa
from tqdm import tqdm
from tensorboardX import SummaryWriter
from PIL import Image
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import socket
import threading
from threading import Lock
import pyaudio
import wave
import struct

from ac.loader import predict_dense
from esclass.loader import predict_resnet
from urban.loader import predict_cnn
from urban.loader import predict_talnet

from urban.model_CNN10TL_training import CNN10Classifier
from urban.model_TALNetV3_training import TALNetV3Classifier
from torchvision.models import resnet34

# Fetch the service account key JSON file contents
cred = credentials.Certificate('../fire.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})

def save(name, channels, rate, frames):
	wf = wave.open(name, 'wb')
	wf.setnchannels(channels)
	wf.setsampwidth(2)
	wf.setframerate(rate)
	wf.writeframes(b''.join(frames))
	wf.close()

def live_classification(model, device, classes, chunk, n):
	global running
	running = True
	while(running):
		if(len(queue) > 0):
			data = queue.pop(0)
			mono = data / 32768
			sprint("Predicted: ", predict_densenet(model, device, classes, mono, SAMPLE_RATE))
			sprint("Queue Length: ", len(queue))
			#print(mono)
			sprint("data ", data[:50])

def live():
	global running
	running = True
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	while True:
		#target_ip = "98.169.167.38"
		#target_port = 5500
		target_ip = "35.186.188.127"
		target_port = 10000
		s.connect((target_ip, target_port))
		break

	CHUNK = 8192 # 512
	audio_format = pyaudio.paInt16
	channels = 1
	RATE = 44100
	cRATE = 22050

	print("Connected to Server")

	fm, f0, f1, f2, f3 = [], [], [], [], []
	n = 25
	global ind
	ind = 0
	i = 0
	data = np.array([])
	
	threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n), daemon=True).start()
	threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n), daemon=True).start()
	threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n), daemon=True).start()

	s.settimeout(5)

	while running:
		try:
			d = s.recv(CHUNK)
			channels = np.frombuffer(data, dtype='float32')
			c0 = channels[0::8].tobytes() #red
			c1 = channels[1::8].tobytes() #green
			c2 = channels[2::8].tobytes() #blue
			c3 = channels[3::8].tobytes() #purple
			if not d: break
			data = np.concatenate([data, np.frombuffer(d, dtype=np.int16)])
			#threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n)).start()

			fm.append(data)

			if i % n == 0 and i != 0:
				ind +=1
				queue.append(data)
				data = np.array([])
				#queue.append([])
				sprint("len", len(queue))
			i+=1

		except Exception as e:
			running=False
			print("Client Disconnected")
			save("combined.wav", 1, RATE, fm)

		        # save("channel0.wav", 1, cRATE, f0)
			# save("channel1.wav", 1, cRATE, f1)
			# save("channel2.wav", 1, cRATE, f2)
			# save("channel3.wav", 1, cRATE, f3)
			s.close()
			print("Done Saving")
			break
	save("combined.wav", 1, RATE, fm)
	s.close()
def sprint(*a, **b):
    """Thread safe print function"""
    with lock:
        print(*a, **b)

CLASS_PATH = '../ESC-classes.txt'
SAMPLE_RATE = 44100
filename = "baby_cry.wav"
# GPU = "1"
global queue
global done
global running
done = False
queue = []
lock = Lock()

print("Preprocessing...")

clip, sr = librosa.load(filename)
#print(clip[100:] * 32768)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
device1 = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")
device2 = torch.device("cuda:2" if torch.cuda.is_available() else "cpu")


############################ densenet
CONFIG_PATH = 'ac/config/esc_densenet.json'
params = utils.Params(CONFIG_PATH)
dense_path = 'ac/checks/model_best_5.pth.tar'
modeld = models.densenet.DenseNet(params.dataset_name, params.pretrained).to(device)
modeld.load_state_dict(torch.load(dense_path)['model'])
modeld.eval()

############################ resnet
resnet_path = 'esclass/esc50resnet.pth'
weights = torch.load(resnet_path, map_location='cpu')
modelr = weights.to(device)
modelr.eval()

mixup_augmenter = Mixup(float(cparams["alpha"]), int(cparams["seed"]))

############################ cnn10
CNN_PATH = "urban/checks/CNN10TL/CNN10TL-epoch306.ckpt"
CNN_HPARAMS = "data/summaries/CNN10TLAllDatasets/logs/default/version_14/hparams.yaml"
cparams = {}
for line in open(CNN_HPARAMS, 'r').read().splitlines():
    k, v = line.split(": ")
    cparams[k] = v

modelc = CNN10Classifier.load_from_checkpoint(
    CNN_PATH, 
    hparams=cparams,
    fold=1
)
modelc = modelc.to(device)
modelc.eval()

############################ talnetv3
TALNET_PATH = 'urban/checks/TALNetV3/TALNetV3-epoch148.ckpt'
TALNET_HPARAMS = "data/summaries/TALNetV3AllDatasets/logs/default/version_9/hparams.yaml"
modelt = TALNetV3Classifier.load_from_checkpoint(TALNET_PATH, hparams=tparams, fold=1)
modelt = modelt.to(device)
modelt.eval()

classes=[]
for c in open(CLASS_PATH, 'r'):
	classes.append(c)

print("Started")

#test(model, device, classes, params)

#print("Predicted: ", predict_dense(model, device, classes, clip, SAMPLE_RATE))

live()


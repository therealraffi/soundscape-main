import torch
import torchvision
import torch.nn as nn
import numpy as np
import json
import utils
import validate
import argparse
import models.densenet
import models.resnet
import models.inception
import time
import dataloaders.datasetaug
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
#import socket.timeout as TimeoutException

# Fetch the service account key JSON file contents
cred = credentials.Certificate('../fire.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})


def evaluate(model, device, test_loader, classes):
	correct = 0
	total = 0
	model.eval()
	with torch.no_grad():
		for batch_idx, data in enumerate(test_loader):
			inputs = data[0].to(device)
			print(inputs.size())
			target = data[1].squeeze(1).to(device)
			outputs = model(inputs)

			_, predicted = torch.max(outputs.data, 1)
			#print(' '.join('%5s' % classes[predicted[j]] for j in range(2)))
			if(len(predicted) == 0 and len(target) == 0):
                                print('Predicted: NONE', 'Actual: NONE')
			elif(len(predicted) == 0):
                        	print('Predicted: NONE', 'Actual:', classes[target[0]])
			elif(len(target) == 0):
                                print('Predicted:', classes[predicted[0]], 'Actual: NONE')
			else:
				print('Predicted:', [classes[j] for j in predicted], 'Actual:', classes[target[0]])
			total += target.size(0)
			correct += (predicted == target).sum().item()

	return (100*correct/total)

def test(model, device, classes, params):

	for i in range(1, params.num_folds+1):
		val_loader = dataloaders.datasetaug.fetch_dataloader("{}validation128mel{}.pkl".format(params.data_dir, i), params.dataset_name, params.batch_size, params.num_workers, 'validation')
		train_loader = dataloaders.datasetaug.fetch_dataloader( "{}training128mel{}.pkl".format(params.data_dir, i), params.dataset_name, params.batch_size, params.num_workers, 'train')

	print(evaluate(model, device, val_loader, classes))
	#print(evaluate(model, device, train_loader, classes))

def predict_dense(model, device, classes, clip, sr):
	inputs = process(clip, sr).to(device)
	outputs = model(inputs)
	_, predicted = torch.max(outputs.data, 1)
	pred = classes[predicted[0]].replace('\n', '')
	pred = [classes[i].replace('\n', '') for i in predicted]

	ref = db.reference('x_and_y')
	ref.child("sound1").child("classification").set(pred)

	#print('Predicted:', pred)
	return pred

def process(clip, sr):
	num_channels = 3
	window_sizes = [25, 50, 100]
	hop_sizes = [10, 25, 50]
	centre_sec = 2.5
	specs = []

	for i in range(num_channels):
		window_length = int(round(window_sizes[i]*SAMPLE_RATE/1000))
		hop_length = int(round(hop_sizes[i]*SAMPLE_RATE/1000))

		clip = torch.Tensor(clip)
		#print(clip[:50])
		#sprint(clip)
		#sprint(clip.shape)
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

def save(name, channels, rate, frames):
	wf = wave.open(name, 'wb')
	wf.setnchannels(channels)
	wf.setsampwidth(2)
	wf.setframerate(rate)
	wf.writeframes(b''.join(frames))
	wf.close()

def receive_server_data():
	while True:
		try:
			data = s.recv(8192)
		except:
			pass

def live_classification(model, device, classes, chunk, n):
	global running
	running = True
	while(running):
		if(len(queue) > 0):
			data = queue.pop(0)
			mono = data / 32768
			sprint("Predicted: ", predict(model, device, classes, mono, SAMPLE_RATE))
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


CONFIG_PATH = 'config/esc_densenet.json'
CLASS_PATH = '../ESC-classes.txt'
WEIGHT_PATH = 'checks/model_best_5.pth.tar'
SAMPLE_RATE = 44100
filename = "baby_cry.wav"
GPU = "1"
global queue
global done
global running
done = False
queue = []
lock = Lock()

print("Preprocessing...")

clip, sr = librosa.load(filename)
#print(clip[100:] * 32768)

params = utils.Params(CONFIG_PATH)

device = torch.device("cuda:"+GPU if torch.cuda.is_available() else "cpu")

model = models.densenet.DenseNet(params.dataset_name, params.pretrained).to(device)
model.load_state_dict(torch.load(WEIGHT_PATH)['model'])
model.eval()

classes=[]
for c in open(CLASS_PATH, 'r'):
	classes.append(c)

print("Started")

#test(model, device, classes, params)

#print("Predicted: ", predict_dense(model, device, classes, clip, SAMPLE_RATE))

live()


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
				print('Predicted:', classes[predicted[0]], 'Actual:', classes[target[0]])
			total += target.size(0)
			correct += (predicted == target).sum().item()

	return (100*correct/total)

def test(model, device, classes, params):

	for i in range(1, params.num_folds+1):
		val_loader = dataloaders.datasetaug.fetch_dataloader("{}validation128mel{}.pkl".format(params.data_dir, i), params.dataset_name, params.batch_size, params.num_workers, 'validation')
		train_loader = dataloaders.datasetaug.fetch_dataloader( "{}training128mel{}.pkl".format(params.data_dir, i), params.dataset_name, params.batch_size, params.num_workers, 'train')

	print(evaluate(model, device, val_loader, classes))
	#print(evaluate(model, device, train_loader, classes))

def predict(model, device, classes, filename):
	inputs = process(filename).to(device)
	outputs = model(inputs)
	_, predicted = torch.max(outputs.data, 1)
	print('Predicted:', classes[predicted[0]])

def process(filename):
	num_channels = 3
	window_sizes = [25, 50, 100]
	hop_sizes = [10, 25, 50]
	centre_sec = 2.5
	specs = []
	clip, sr = librosa.load(filename, sr=SAMPLE_RATE)

	for i in range(num_channels):
		window_length = int(round(window_sizes[i]*SAMPLE_RATE/1000))
		hop_length = int(round(hop_sizes[i]*SAMPLE_RATE/1000))

		clip = torch.Tensor(clip)
		spec = torchaudio.transforms.MelSpectrogram(SAMPLE_RATE, n_fft=4410, win_length=window_length, hop_length=hop_length, n_mels=128)(clip)
		eps = 1e-6
		spec = spec.numpy()
		spec = np.log(spec+ eps)
		spec = np.asarray(torchvision.transforms.Resize((128, 250))(Image.fromarray(spec)))
		specs.append(spec)

	specs = np.array(specs)
	values = torch.Tensor(specs)
	values = values.reshape(1, 3, 128, 250)

	return values

if __name__ == "__main__":
	CONFIG_PATH = 'config/esc_densenet.json'
	CLASS_PATH = '../ESC-classes.txt'
	WEIGHT_PATH = 'checks/model_best_1.pth.tar'
	SAMPLE_RATE = 44100
	GPU = "0"

	print("Preprocessing...")

	params = utils.Params(CONFIG_PATH)

	device = torch.device("cuda:"+GPU if torch.cuda.is_available() else "cpu")

	model = models.densenet.DenseNet(params.dataset_name, params.pretrained).to(device)
	model.load_state_dict(torch.load(WEIGHT_PATH)['model'])
	model.eval()

	classes=[]
	for c in open(CLASS_PATH, 'r'):
		classes.append(c)

	filename = "../ESC50/audio/2-54962-A-23.wav"
	#test(model, device, classes, params)
	print('Classification')
	predict(model, device, classes, filename)

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

from tqdm import tqdm
from tensorboardX import SummaryWriter

def evaluate(model, device, test_loader):
	classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog', 'frog', 'horse', 'ship', 'truck','dog')
	correct = 0
	total = 0
	model.eval()
	with torch.no_grad():
		for batch_idx, data in enumerate(test_loader):
			inputs = data[0].to(device)
			target = data[1].squeeze(1).to(device)

			outputs = model(inputs)

			_, predicted = torch.max(outputs.data, 1)
			print(' '.join('%5s' % classes[target[j]] for j in range(4)))
			total += target.size(0)
			correct += (predicted == target).sum().item()

	return (100*correct/total)


path = "config/esc_densenet.json"
wpath = "checks/model_best_1.pth.tar"
params = utils.Params(path)
gpu = "0"


device = torch.device("cuda:"+gpu if torch.cuda.is_available() else "cpu")
for i in range(1, params.num_folds+1):
    if params.dataaug:
        val_loader = dataloaders.datasetaug.fetch_dataloader("{}validation128mel{}.pkl".format(params.data_dir, i), params.dataset_name, params.batch_size, params.num_workers, 'validation')
model = models.densenet.DenseNet(params.dataset_name, params.pretrained).to(device)
model.load_state_dict(torch.load(wpath)['model'])

print(evaluate(model, device, val_loader))

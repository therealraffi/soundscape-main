from common import *
import pyaudio
import sys
import time
import array
import numpy as np
import queue
from collections import deque
import argparse
import socket
import pyaudio
import wave

parser = argparse.ArgumentParser(description='Run sound classifier')
parser.add_argument('--input', '-i', default='0', type=int,
                    help='Audio input device index. Set -1 to list devices')
parser.add_argument('--input-file', '-f', default='', type=str,
                    help='If set, predict this audio file.')
#parser.add_argument('--save_file', default='recorded.wav', type=str,
#                    help='File to save samples captured while running.')
parser.add_argument('--model-pb-graph', '-pb', default='', type=str,
                    help='Feed model you want to run, or conf.runtime_weight_file will be used.')
args = parser.parse_args()

#Capture & pridiction jobs
fram, fra0, fra1, fra2, fra3 = queue.Queue(maxsize=100), queue.Queue(maxsize=100), queue.Queue(maxsize=100), queue.Queue(maxsize=100), queue.Queue(maxsize=100)
#record
recm, rec0, rec1, rec2, rec3 = [], [], [], [], []
#audio buffer
buffm, buff0, buff1, buff2, buff3 = [], [], [], [], []
#pred queue
predm, pred0, pred1, pred2, pred3 = deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles)

save0 = time.time()

def on_predicted(ensembled_pred, num):
    result = np.argmax(ensembled_pred)
    print(num, conf.labels[result], ensembled_pred[result], int((time.time() - save0)*1000)/1000)

def main_process(model, on_predicted):
    # Pool audio data
    global buffm
    global fram
    global predm
    while not fram.empty():
        buffm.extend(fram.get())
        if len(buffm) >= conf.mels_convert_samples: break
    if len(buffm) < conf.mels_convert_samples: return
    # Convert to log mel-spectrogram
    audio_to_convert = np.array(buffm[:conf.mels_convert_samples]) / 32767
    buffm = buffm[conf.mels_onestep_samples:]
    mels = audio_to_melspectrogram(conf, audio_to_convert)
    # Predict, ensemble
    X = []
    for i in range(conf.rt_process_count):
        cur = int(i * conf.dims[1] / conf.rt_oversamples)
        X.append(mels[:, cur:cur+conf.dims[1], np.newaxis])
    X = np.array(X)
    samplewise_normalize_audio_X(X)
    raw_preds = model.predict(X)
    for raw_pred in raw_preds:
        predm.append(raw_pred)
        ensembled_pred = geometric_mean_preds(np.array([pred for pred in predm]))
        on_predicted(ensembled_pred, "m")

def main_process0(model, on_predicted):
    # Pool audio data
    global buff0
    global fra0
    global pred0
    while not fra0.empty():
        buff0.extend(fra0.get())
        if len(buff0) >= conf.mels_convert_samples: break
    if len(buff0) < conf.mels_convert_samples: return
    # Convert to log mel-spectrogram
    audio_to_convert = np.array(buff0[:conf.mels_convert_samples]) / 32767
    buff0 = buff0[conf.mels_onestep_samples:]
    mels = audio_to_melspectrogram(conf, audio_to_convert)
    # Predict, ensemble
    X = []
    for i in range(conf.rt_process_count):
        cur = int(i * conf.dims[1] / conf.rt_oversamples)
        X.append(mels[:, cur:cur+conf.dims[1], np.newaxis])
    X = np.array(X)
    samplewise_normalize_audio_X(X)
    raw_preds = model.predict(X)
    for raw_pred in raw_preds:
        pred0.append(raw_pred)
        ensembled_pred = geometric_mean_preds(np.array([pred for pred in pred0]))
        on_predicted(ensembled_pred, 0)

def main_process1(model, on_predicted):
    # Pool audio data
    global buff1
    global fra1
    global pred1
    while not fra1.empty():
        buff1.extend(fra1.get())
        if len(buff1) >= conf.mels_convert_samples: break
    if len(buff1) < conf.mels_convert_samples: return
    # Convert to log mel-spectrogram
    audio_to_convert = np.array(buff1[:conf.mels_convert_samples]) / 32767
    buff1 = buff1[conf.mels_onestep_samples:]
    mels = audio_to_melspectrogram(conf, audio_to_convert)
    # Predict, ensemble
    X = []
    for i in range(conf.rt_process_count):
        cur = int(i * conf.dims[1] / conf.rt_oversamples)
        X.append(mels[:, cur:cur+conf.dims[1], np.newaxis])
    X = np.array(X)
    samplewise_normalize_audio_X(X)
    raw_preds = model.predict(X)
    for raw_pred in raw_preds:
        pred1.append(raw_pred)
        ensembled_pred = geometric_mean_preds(np.array([pred for pred in pred1]))
        on_predicted(ensembled_pred, 1)

def main_process2(model, on_predicted):
    # Pool audio data
    global buff2
    global fra2
    global pred2
    while not fra2.empty():
        buff2.extend(fra2.get())
        if len(buff2) >= conf.mels_convert_samples: break
    if len(buff2) < conf.mels_convert_samples: return
    # Convert to log mel-spectrogram
    audio_to_convert = np.array(buff2[:conf.mels_convert_samples]) / 32767
    buff2 = buff2[conf.mels_onestep_samples:]
    mels = audio_to_melspectrogram(conf, audio_to_convert)
    # Predict, ensemble
    X = []
    for i in range(conf.rt_process_count):
        cur = int(i * conf.dims[1] / conf.rt_oversamples)
        X.append(mels[:, cur:cur+conf.dims[1], np.newaxis])
    X = np.array(X)
    samplewise_normalize_audio_X(X)
    raw_preds = model.predict(X)
    for raw_pred in raw_preds:
        pred2.append(raw_pred)
        ensembled_pred = geometric_mean_preds(np.array([pred for pred in pred2]))
        on_predicted(ensembled_pred, 2)

def main_process3(model, on_predicted):
    # Pool audio data
    global buff3
    global fra3
    global pred3
    while not fra3.empty():
        buff3.extend(fra3.get())
        if len(buff3) >= conf.mels_convert_samples: break
    if len(buff3) < conf.mels_convert_samples: return
    # Convert to log mel-spectrogram
    audio_to_convert = np.array(buff3[:conf.mels_convert_samples]) / 32767
    buff3 = buff3[conf.mels_onestep_samples:]
    mels = audio_to_melspectrogram(conf, audio_to_convert)
    # Predict, ensemble
    X = []
    for i in range(conf.rt_process_count):
        cur = int(i * conf.dims[1] / conf.rt_oversamples)
        X.append(mels[:, cur:cur+conf.dims[1], np.newaxis])
    X = np.array(X)
    samplewise_normalize_audio_X(X)
    raw_preds = model.predict(X)
    for raw_pred in raw_preds:
        pred3.append(raw_pred)
        ensembled_pred = geometric_mean_preds(np.array([pred for pred in pred3]))
        on_predicted(ensembled_pred, 3)

# # Main controller
def process_file(model, filename, on_predicted=on_predicted):
    # Feed audio data as if it was recorded in realtime
    audio = read_audio(conf, filename, trim_long_data=False) * 32767
    while len(audio) > conf.rt_chunk_samples:
        fram.put(audio[:conf.rt_chunk_samples])
        audio = audio[conf.rt_chunk_samples:]
        main_process(model, on_predicted)

def my_exit(model):
    model.close()
    exit(0)

def get_model(graph_file):
    model_node = {
        'alexnet': ['import/conv2d_1_input',
                    'import/batch_normalization_1/keras_learning_phase',
                    'import/output0'],
        'mobilenetv2': ['import/input_1',
                        'import/bn_Conv1/keras_learning_phase',
                        'import/output0']
    }
    return KerasTFGraph(
        conf.runtime_model_file if graph_file == '' else graph_file,
        input_name=model_node[conf.model][0],
        keras_learning_phase_name=model_node[conf.model][1],
        output_name=model_node[conf.model][2])

def saveaudio(name, channel, rate, arr):
    FORMAT = pyaudio.paInt16
    wf = wave.open(name, 'wb')
    wf.setnchannels(channel)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(b''.join(arr))
    wf.close()

# Socket
HOST = "192.168.1.218"
PORT = 10000

# Audio
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (HOST, PORT)
sock.bind(server_address)
sock.listen(1)

CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 4
RATE = 44100
cRATE = 22050

stream = True
model = get_model(args.model_pb_graph)
while stream:
    connection, client_address = sock.accept()
    data = connection.recv(8192)
    while data != "":
        try:
            # print(time.time())
            data = connection.recv(8192)
            channels = np.fromstring(data, dtype='int16')

            t0 = channels[0::8].tostring()
            t1 = channels[1::8].tostring()
            t2 = channels[2::8].tostring()
            t3 = channels[3::8].tostring()

            recm.append(data)
            rec0.append(t0)
            rec1.append(t1)
            rec2.append(t2)
            rec3.append(t3)

            wavem = array.array('h', data)
            wave0 = array.array('h', t0)
            wave1 = array.array('h', t1)
            wave2 = array.array('h', t2)
            wave3 = array.array('h', t3)

            fram.put(wavem, True)
            fra0.put(wave0, True)
            fra1.put(wave1, True)
            fra2.put(wave2, True)
            fra3.put(wave3, True)
            #combined
            main_process(model, on_predicted)
            # channel 0
            # main_process0(model, on_predicted)
            #channel 1
            # main_process1(model, on_predicted)
            #channel 2
            # main_process2(model, on_predicted)
            #channel 3
            # main_process3(model, on_predicted)
            # time.sleep(0.001)
        except KeyboardInterrupt as e:
            print("Saving...")

            saveaudio("class.wav", 4, RATE, recm)
            saveaudio("out0.wav", 1, cRATE, rec0)
            saveaudio("out1.wav", 1, cRATE, rec1)
            saveaudio("out2.wav", 1, cRATE, rec2)
            saveaudio("out3.wav", 1, cRATE, rec3)

            print("End")
            my_exit(model)
            print("done")
            stream = False
            break

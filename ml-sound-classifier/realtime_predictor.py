#-*-coding:utf-8-*-
#!/usr/bin/python
#
# Run sound classifier in realtime.
#
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

# # Capture & pridiction jobs
buff0, buff1, buff2, buff3, buff4 = [], [], [], [], []
pred0, pred1, pred2, pred3, pred4 = deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles), deque(maxlen=conf.pred_ensembles)

raw_frames, c0, c1, c2, c3 = queue.Queue(maxsize=100), queue.Queue(maxsize=100), queue.Queue(maxsize=100), queue.Queue(maxsize=100), queue.Queue(maxsize=100)
sep = []
f0, f1, f2, f3 = [], [], [], []

def callback(in_data, frame_count, time_info, status):
    sep.append(in_data)
    channels = np.fromstring(in_data, dtype='int16')

    t0 = channels[0::8].tostring()
    t1 = channels[1::8].tostring()
    t2 = channels[2::8].tostring()
    t3 = channels[3::8].tostring()

    f0.append(t0)
    f1.append(t1)
    f2.append(t2)
    f3.append(t3)

    wave = array.array('h', in_data)
    wave0 = array.array('h', t0)
    wave1 = array.array('h', t1)
    wave2 = array.array('h', t2)
    wave3 = array.array('h', t3)

    raw_frames.put(wave, True)
    c0.put(wave0, True)
    c1.put(wave1, True)
    c2.put(wave2, True)
    c3.put(wave3, True)

    return (None, pyaudio.paContinue)

def on_predicted(ensembled_pred, num):
    result = np.argmax(ensembled_pred)
    print(num, conf.labels[result], ensembled_pred[result])

def main_process(model, frames, on_predicted, num):
    # Pool audio data
    global buff0
    while not frames.empty():
        buff0.extend(frames.get())
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
        on_predicted(ensembled_pred, num)

def main_process1(model, frames, on_predicted, num):
    # Pool audio data
    global buff1
    while not frames.empty():
        buff1.extend(frames.get())
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
        on_predicted(ensembled_pred, num)

def main_process2(model, frames, on_predicted, num):
    # Pool audio data
    global buff2
    while not frames.empty():
        buff2.extend(frames.get())
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
        on_predicted(ensembled_pred, num)

# # Main controller
def process_file(model, frames, filename, on_predicted=on_predicted):
    # Feed audio data as if it was recorded in realtime
    audio = read_audio(conf, filename, trim_long_data=False) * 32767
    while len(audio) > conf.rt_chunk_samples:
        frames.put(audio[:conf.rt_chunk_samples])
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

def saveaudio(name, channel, rate, arr, audio):
    FORMAT = pyaudio.paInt16
    wf = wave.open(name, 'wb')
    wf.setnchannels(channel)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(rate)
    wf.writeframes(b''.join(arr))
    wf.close()

def run_predictor():
    model = get_model(args.model_pb_graph)
    # file mode
    if args.input_file != '':
        process_file(model, raw_frames, args.input_file)
        # process_file(model, raw_frames, args.input_file)
        # process_file(model, raw_frames, args.input_file)
        # process_file(model, raw_frames, args.input_file)
        # process_file(model, raw_frames, args.input_file)
        print("preprocessed")
        my_exit(model)
    # device list display mode
    if args.input < 0:
        print_pyaudio_devices()
        my_exit(model)
    # Socket
    HOST = "192.168.1.218"
    PORT = 10000
    # normal: realtime mode
    p = pyaudio.PyAudio()
    CHUNK = 1024 * 4
    FORMAT = pyaudio.paInt16
    CHANNELS = 4
    RATE = 44100
    cRATE = 22050
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    start=False,
                    stream_callback=callback)

    # main loop
    stream.start_stream()
    while stream.is_active():
        try:
            main_process(model, raw_frames, on_predicted, 0)
            main_process1(model, c0, on_predicted, 1)
            main_process2(model, c1, on_predicted, 2)
            # main_process3(model, c2, on_predicted, 3)
            # main_process4(model, c3, on_predicted, 4)
            # time.sleep(0.001)
        except KeyboardInterrupt as e:
            print("Wow")

            saveaudio("class.wav", CHANNELS, RATE, sep, p)
            saveaudio("out0.wav", 1, cRATE, f0, p)
            saveaudio("out1.wav", 1, cRATE, f1, p)
            saveaudio("out2.wav", 1, cRATE, f2, p)
            saveaudio("out3.wav", 1, cRATE, f3, p)

            print("End")
            stream.stop_stream()
            stream.close()
            p.terminate()
            my_exit(model)
            break

if __name__ == '__main__':
    run_predictor()

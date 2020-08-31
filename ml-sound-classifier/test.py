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
raw_frames = queue.Queue(maxsize=100)
sep = []
f0, f1, f2, f3 = [], [], [], []

def callback(in_data, frame_count, time_info, status):
    sep.append(in_data)
    channels = np.fromstring(in_data, dtype='int16')
    f0.append(channels[0::8].tostring())
    f1.append(channels[1::8].tostring())
    f2.append(channels[2::8].tostring())
    f3.append(channels[3::8].tostring())
    wave = array.array('h', in_data)
    raw_frames.put(wave, True)
    return (None, pyaudio.paContinue)

def on_predicted(ensembled_pred):
    result = np.argmax(ensembled_pred)
    print(conf.labels[result], ensembled_pred[result])

raw_audio_buffer = []
pred_queue = deque(maxlen=conf.pred_ensembles)
def main_process(model, on_predicted):
    # Pool audio data
    global raw_audio_buffer
    while not raw_frames.empty():
        raw_audio_buffer.extend(raw_frames.get())
        if len(raw_audio_buffer) >= conf.mels_convert_samples: break
    if len(raw_audio_buffer) < conf.mels_convert_samples: return
    # Convert to log mel-spectrogram
    audio_to_convert = np.array(raw_audio_buffer[:conf.mels_convert_samples]) / 32767
    raw_audio_buffer = raw_audio_buffer[conf.mels_onestep_samples:]
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
        pred_queue.append(raw_pred)
        ensembled_pred = geometric_mean_preds(np.array([pred for pred in pred_queue]))
        on_predicted(ensembled_pred)

# # Main controller
def process_file(model, filename, on_predicted=on_predicted):
    # Feed audio data as if it was recorded in realtime
    audio = read_audio(conf, filename, trim_long_data=False) * 32767
    while len(audio) > conf.rt_chunk_samples:
        raw_frames.put(audio[:conf.rt_chunk_samples])
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

def run_predictor():
    model = get_model(args.model_pb_graph)
    # file mode
    if args.input_file != '':
        process_file(model, args.input_file)
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
    RATE = 22050 * 2
    cRATE = 11025 * 2
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
            main_process(model, on_predicted)
            # time.sleep(0.001)
        except KeyboardInterrupt as e:
            print("Wow")

            wf = wave.open("class.wav", 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(sep))
            wf.close()

            wf = wave.open('out0.wav', 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(cRATE)
            wf.writeframes(b''.join(f0))
            wf.close()

            wf1 = wave.open('out1.wav', 'wb')
            wf1.setnchannels(1)
            wf1.setsampwidth(p.get_sample_size(FORMAT))
            wf1.setframerate(cRATE)
            wf1.writeframes(b''.join(f1))
            wf1.close()

            wf2 = wave.open('out2.wav', 'wb')
            wf2.setnchannels(1)
            wf2.setsampwidth(p.get_sample_size(FORMAT))
            wf2.setframerate(cRATE)
            wf2.writeframes(b''.join(f2))
            wf2.close()

            wf3 = wave.open('out3.wav', 'wb')
            wf3.setnchannels(1)
            wf3.setsampwidth(p.get_sample_size(FORMAT))
            wf3.setframerate(cRATE)
            wf3.writeframes(b''.join(f3))
            wf3.close()

            print("End")
            stream.stop_stream()
            stream.close()
            p.terminate()
            my_exit(model)
            break

if __name__ == '__main__':
    run_predictor()
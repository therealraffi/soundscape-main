import re
import sys
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from google.cloud import speech
import pyaudio
from six.moves import queue
import socket
import wave
import numpy as np
import threading

#Firebase
cred = credentials.Certificate('soundy-8d98a-firebase-adminsdk-o03jf-c7fede8ea2.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})
ref = db.reference('Sound')

# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 44100//2
CHUNK_SIZE = 8192  # 100ms

#Streaming Client
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while True:
    try:
        target_ip = "173.66.155.183"
        target_port = 10000
        s.connect((target_ip, target_port))
        break
    except:
        print("Couldn't connect to server")

def get_current_time():
    return int(round(time.time() * 1000))

fm = []
f0 = []
mic = []

class ResumableMicrophoneStream:
    def __init__(self, rate, chunk_size):
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True
        self._audio_interface = pyaudio.PyAudio()
        # self._audio_stream = self.sound
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input_device_index=3,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._fill_buffer
        )

    def __enter__(self):
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, *args, **kwargs):
        global fm
        global mic

        # print(len(fm), len(self.audio_input))
        # self._buff.put(fm[-1])

        # channels = np.frombuffer(fm[-1], dtype='int16')
        # c0 = channels[0::8].tobytes()
        mic.append(b''.join(f0[-70:]))
        # print(len(f0), len(mic), len(self.audio_input))
        
        self._buff.put(mic[-1])

        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            data = []
            if self.new_stream and self.last_audio_input:
                chunk_time = STREAMING_LIMIT / len(self.last_audio_input)
                if chunk_time != 0:
                    if self.bridging_offset < 0:
                        self.bridging_offset = 0
                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time
                    chunks_from_ms = round(
                        (self.final_request_end_time - self.bridging_offset)
                        / chunk_time
                    )
                    self.bridging_offset = round(
                        (len(self.last_audio_input) - chunks_from_ms) * chunk_time
                    )
                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])
                self.new_stream = False

            chunk = self._buff.get()
            # chunk = s.recv(8192)
            self.audio_input.append(chunk)
            if chunk is None:
                return

            data.append(chunk)

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                    self.audio_input.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)

finalspeech = ""

def listen_print_loop(responses, stream):
    global finalspeech  
    for response in responses:
        if get_current_time() - stream.start_time > STREAMING_LIMIT:
            stream.start_time = get_current_time()
            break
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        finalspeech = transcript

        result_seconds = 0
        result_micros = 0

        if result.result_end_time.seconds:
            result_seconds = result.result_end_time.seconds
        if result.result_end_time.microseconds:
            result_micros = result.result_end_time.microseconds
        stream.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

        corrected_time = (
            stream.result_end_time
            - stream.bridging_offset
            + (STREAMING_LIMIT * stream.restart_counter)
        )
        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.

        if result.is_final:
            sys.stdout.write("\033[K")
            # sys.stdout.write(str(corrected_time) + ": " + transcript + "\n")
            sys.stdout.write(transcript + "\n")

            stream.is_final_end_time = stream.result_end_time
            stream.last_transcript_was_final = True
            ref.child("sound1").child("content").set(finalspeech)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                sys.stdout.write("Exiting...\n")
                stream.closed = True
                break
        else:
            sys.stdout.write("\033[K")
            # sys.stdout.write(str(corrected_time) + ": " + transcript + "\r")
            sys.stdout.write(transcript + "\r")
            stream.last_transcript_was_final = False

def save(name, channels, rate, frames):
    wf = wave.open(name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def sound():
    global s
    global fm
    while not exit_signal.is_set():
        while True:
            data = s.recv(8192)
            fm.append(data)

            channels = np.frombuffer(data, dtype='int16')
            c0 = channels[0::8].tobytes()
            f0.append(c0)

            # channels = np.frombuffer(fm[-1], dtype='int16')
            # c0 = channels[0::8].tobytes()

def main():
    """start bidirectional streaming from microphone input to speech API"""
    while not exit_signal.is_set():
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-US",
            max_alternatives=1,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
        print("Start Voice Recognition")

        with mic_manager as stream:
            try:
                while not stream.closed:
                    stream.audio_input = []
                    audio_generator = stream.generator()

                    requests = (
                        speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator
                    )

                    responses = client.streaming_recognize(streaming_config, requests)

                    listen_print_loop(responses, stream)

                    if stream.result_end_time > 0:
                        stream.final_request_end_time = stream.is_final_end_time
                    stream.result_end_time = 0
                    stream.last_audio_input = []
                    stream.last_audio_input = stream.audio_input
                    stream.audio_input = []
                    stream.restart_counter = stream.restart_counter + 1
                    if not stream.last_transcript_was_final:
                        sys.stdout.write("\n")
                    stream.new_stream = True
            except KeyboardInterrupt:
                pass         

exit_signal = threading.Event()  # your global exit signal

t1 = threading.Thread(target=main) 
t2 = threading.Thread(target=sound) 

t1.start() 
t2.start() 

try:
    while not exit_signal.is_set(): 
        time.sleep(0.1)  
except KeyboardInterrupt:  
    exit_signal.set()  
    save("speech.wav", 4, 44100, fm)   
    save("mic.wav", 1, 44100//2, mic)   
    print("Saved")
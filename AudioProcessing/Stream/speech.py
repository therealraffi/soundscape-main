import re
import sys
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from google.cloud import speech
from six.moves import queue
import socket
import wave
import numpy as np
import threading
import os

# os.system("export GOOGLE_APPLICATION_CREDENTIALS='/Users/nafi/Develop/GitHub/ISEF2021/AudioProcessing/Stream/Audio-33662799f829.json'")

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

#Global Vars
fm = []
channelframes = [[], [], [], []]
finalspeech = ""

while True:
    try:
        target_ip = "173.66.155.183"
        target_port = 10000
        s.connect((target_ip, target_port))
        break
    except:
        print("Couldn't connect to server")

def getsound():
    global fm
    while True:
        data = s.recv(8192)
        fm.append(data)

def get_current_time():
    return int(round(time.time() * 1000))

class ResumableMicrophoneStream:
    def __init__(self, rate, chunk_size, channelnum):
        def init():
            self._rate = rate
            self.channelnum = channelnum
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
            self.prevlen = 0

        def sound():
            global fm
            while True:
                if self.prevlen != len(fm):                
                    back = len(fm) - self.prevlen
                    self.prevlen = len(fm)

                    fc = channelframes[self.channelnum]
                    channels = np.frombuffer(b''.join(fm[-back:]), dtype='int16')
                    channels = channels[self.channelnum::8].tobytes()
                    fc.append(channels)

                    # print([len(i) for i in channelframes], len(fm), back)

                    self._fill_buffer(channels)

        t1 = threading.Thread(target=init) 
        t2 = threading.Thread(target=sound) 

        t1.start() 
        t2.start() 

    def __enter__(self):
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self.closed = True
        self._buff.put(None)

    def _fill_buffer(self, in_data, *args, **kwargs):
        self._buff.put(in_data)
        return None, None

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

def listen_print_loop(responses, stream, channelnum):
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

        ref.child("sound" + str(channelnum + 1)).child("content").set(transcript)

        if result.is_final:
            #where speech is finalized
            print(channelnum, transcript)

            #Temp sys.stdout.write("\033[K")
            
            # sys.stdout.write(str(corrected_time) + ": " + transcript + "\n")

            #Temp sys.stdout.write(transcript + "\n")

            stream.is_final_end_time = stream.result_end_time
            stream.last_transcript_was_final = True

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                #Temp sys.stdout.write("Exiting...\n")
                stream.closed = True
                break
        else:
            #Temp sys.stdout.write("\033[K")
            # sys.stdout.write(str(corrected_time) + ": " + transcript + "\r")
            #Temp sys.stdout.write(transcript + "\r")
            stream.last_transcript_was_final = False

def save(name, channels, rate, frames):
    wf = wave.open(name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def main(channelnum):
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

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE, channelnum)
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

                listen_print_loop(responses, stream, channelnum)

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
            return         

if __name__ == "__main__": 
    t0 = threading.Thread(target=getsound)
    t1 = threading.Thread(target=main, kwargs={'channelnum': 0})
    t2 = threading.Thread(target=main, kwargs={'channelnum': 1})
    t3 = threading.Thread(target=main, kwargs={'channelnum': 2})
    t4 = threading.Thread(target=main, kwargs={'channelnum': 3})

    try:
        t0.start()
        t1.start() 
        t2.start() 
        t3.start() 
        t4.start() 

        t0.join()
        t1.join() 
        t2.join() 
        t3.join() 
        t4.join() 
    except:
        save("speech.wav", 4, 44100, fm)   
        save("speechchannel0.wav", 1, 44100//2, channelframes[0])  
        save("speechchannel1.wav", 1, 44100//2, channelframes[1]) 
        save("speechchannel2.wav", 1, 44100//2, channelframes[2]) 
        save("speechchannel3.wav", 1, 44100//2, channelframes[3])  

        print("\n\nSaved\n\n\n\n\n\nEnd")
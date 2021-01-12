import socket
import threading
import pyaudio
import numpy as np
import re
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import math
import struct
import serial
from google.cloud import speech
from six.moves import queue
import time
import sys
import matplotlib.pyplot as plt

#Local IP
ip = socket.gethostbyname(socket.gethostname())

#Firebase
cred = credentials.Certificate('soundy-8d98a-firebase-adminsdk-o03jf-c7fede8ea2.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})

#Global Data Vars
graphdata = b""
sepdata = b""
postdata = b""
running = True
angles = []
analysis = []
fm = []
channelframes = [[], [], [], []]
finalspeech = ""
ref = db.reference('Sound')

# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 44100//2
CHUNK_SIZE = 8192  # 100ms

def sep():
    global sepdata
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            target_ip = "35.186.188.127"
            target_port = 10000
            s.connect((target_ip, target_port))
            break
        except:
            print("Couldn't connect to server 9000")

    while running:
        try:
            sepdata = s.recv(8192)
        except Exception as e:
            s.close()
            pass
    s.close()

def post():
    global postdata
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            target_ip = "35.186.188.127"
            target_port = 10010
            s.connect((target_ip, target_port))
            break
        except:
            print("Couldn't connect to server 9000")

    while running:
        try:
            postdata = s.recv(8192)
        except Exception as e:
            s.close()
            pass
    s.close()

def position():
    global graphdata
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            target_ip = "35.186.188.127"
            target_port = 9000
            s.connect((target_ip, target_port))
            break
        except:
            print("Couldn't connect to server 9000")

    while running:
        try:
            graphdata = s.recv(8192)
        except Exception as e:
            s.close()
            pass
    s.close()

def getanalysis():
    global analysis
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            target_ip = "35.186.188.127"
            target_port = 10050
            s.connect((target_ip, target_port))
            break
        except:
            print("Couldn't connect to server 10050")

    while running:
        try:
            data = s.recv(512)
            if data != b'':
                analysis = eval("[[" + re.findall(r'\[\[(.*?)\]\]', data.decode())[0] + "]]")
        except Exception as e:
            s.close()
            # print(e)
            pass
    s.close()

def firejson(plot, colors):
    visible = ['false'] * 4
    for i in colors:
        visible[int(i[1])] = 'true'

    out = ""
    plotind = 0

    for i in range(4):
        if visible[i] == 'false':
            out += "'sound%s': {'cords': '%f %f', 'visibility' : 'false'}, " % (i + 1, 0, 0)
        else:
            col = colors[plotind]
            out += "'sound%s': {'cords': '%f %f', 'visibility' : 'true'}, " % (i + 1, plot[plotind][0], plot[plotind][1])
            plotind += 1
    
    return "{" + out[:-2] + "}"

def graph():
    global graphdata
    global angles
    global running

    firecoord = db.reference('x_and_y')   
    while running:
        try:
            coord = graphdata.decode().replace("\n", "")
            result = re.search(r'\[(.*?)\]', coord).group(1)
            xc = re.findall(r'"x": (.*?),', result)
            yc = re.findall(r'"y": (.*?),', result)
            zc = re.findall(r'"z": (.*?),', result)
            points = []
            ind = []
            colors = ["r0", "g1", "b2", "m3"]

            for i in range(len(xc)):
                x = float(xc[i])
                y = float(yc[i])
                z = float(zc[i])
                if x != 0 and y != 0 and z != 0:
                    theta = math.atan(y/x)
                    x = abs(math.cos(theta)) * x / abs(x) * -1
                    y = abs(math.sin(theta)) * y / abs(y)
                    points.append([x, y])
                    ind.append(colors[i])

            points = np.array(points)
            plot = []
            temp = []
            
            for i in range(len(points)):
                angle = math.atan2(points[i][1], points[i][0]) * 180 / math.pi + 60
                if angle < 0:
                    angle += 360
                temp.append([angle, int(ind[i][1])])
                angle *= math.pi/180

                plot.append([math.cos(angle), math.sin(angle)])
            angles = temp

            #Firebase
            fire = eval(firejson(plot, ind))
            firecoord.set(fire)
        except KeyboardInterrupt as e:
            pass
        except Exception as e:
            pass

def sig(num):
    return 1/(1 + math.exp(-20 * num))

def amplitude(block):
    count = len(block)/2

    if count == 0:
        return None

    count = count if count != 0 else 1
    format = "%dh"%(count)
    shorts = struct.unpack(format, block)

    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768.0)
        sum_squares += n**2
        
    # return 100 * (sum_squares/count) ** 0.5
    return int(2 * (100 * sig((sum_squares/count) ** 0.5) - 50))

def avgfreq(block):
        result = np.frombuffer(block, dtype=np.int16)

        if len(result) == 0:
            return None

        w = np.fft.fft(result)
        freqs = np.abs((np.fft.fftfreq(len(w))*44100))
        w = np.abs(w)
        indices = np.argsort(w)[int(len(w)*0.99):]
        bin_const = 1
        indices = indices[len(indices) % bin_const:]
        w = w[indices]
        freqs = freqs[indices]
        w = w[np.argsort(freqs)]
        freqs = np.sort(freqs)
        w = np.reshape(w, (-1, bin_const)).sum(axis=1)
        freqs = np.average(np.reshape(freqs, (-1, bin_const)), axis=1)
        w = w / np.sum(w)
        
        freqdict = dict(zip(freqs, w))
        freqdict = {k:v for k, v in freqdict.items() if v * 100 > 1}
        
        wsum = sum(freqdict.values())
        wsum = wsum if wsum != 0 else 1

        # print()
        # for i in freqdict:
        #     print(int(i), "\t", freqdict[i] * 100 / wsum)
        # print()

        out = 0
        for i in freqdict:
            out += i * freqdict[i] / wsum

        return None if math.isnan(float(out)) or len(freqdict) == 0 else max(1, int(out/2))

def arduino():
    global sepdata
    global postdata
    global angles
    global analysis
    global running

    ardlow = serial.Serial(port='/dev/tty.usbserial-14111340', baudrate=115200)
    ardhigh = serial.Serial(port='/dev/tty.usbserial-14111330', baudrate=115200)

    while running:
        try:
            channels = np.frombuffer(postdata, dtype='int16')
            c0 = channels[0::8].tobytes() #red
            c1 = channels[1::8].tobytes() #green
            c2 = channels[2::8].tobytes() #blue
            c3 = channels[3::8].tobytes() #purple

            # analysis = [[amplitude(c0), avgfreq(c0)], [amplitude(c1), avgfreq(c1)], [amplitude(c2), avgfreq(c2)], [amplitude(c3), avgfreq(c3)]]
            ignore = 90

            for c in range(len(angles) - 1, -1, -1):
                i = angles[c]
                if (180 - ignore)/2 < i[0] < (180 + ignore)/2:
                    del angles[c]

            motors = [0] * 6
            inc = (360 - ignore) / 5

            possible = [(180 + ignore)/2 + i * inc for i in range(5)]
            possible.insert(0, (180 - ignore)/2)

            for angle, channel in angles:
                ind = 0
                for c, k in enumerate(possible):
                    if k - inc/2 <= angle <= k + inc/2:
                        ind = c
                        if motors[ind] != 0:
                            if ind == 5:
                                if motors[0] == 0:
                                    ind = 0
                                    break
                                if motors[4] == 0:
                                    ind = 4
                                    break
                            else:
                                if motors[ind + 1] == 0:
                                    ind += 1
                                    break
                                if motors[ind - 1] == 0:
                                    ind -= 1
                                    break
                        else:
                            break
                #amplitude should be between 0 and 100 since arduino mulplies pwm by 2.55
                motors[ind] = [max(analysis[channel][0] * 90/100, 0), analysis[channel][1]] if analysis[channel][0] > 0 else 0

            # print(angles)
            # print(analysis)
            # print(motors)
            # print("\n\n")
            # amp = max(analysis[0][0], analysis[1][0], analysis[2][0], analysis[3][0])
            amp = amplitude(postdata)

            print("%3s %6s \t %3s %6s \t %3s %6s \t %3s %6s" % (analysis[0][0], analysis[0][1], analysis[1][0], analysis[1][1], analysis[2][0], analysis[2][1], analysis[3][0], analysis[3][1]), amp * "|")

            low = [0] * 6
            high = [0] * 6

            for c, i in enumerate(motors):
                if i == 0:
                    continue
                elif i[1] > 640:
                    high[c] = i[0]
                else:
                    low[c] = i[0]

            # print(high)
            # print(low)

            out = "<%s, %s, %s, %s, %s, %s>" % (low[1], low[2], low[3], low[4], low[5], low[0])
            ardlow.write(out.encode())
            
            out = "<%s, %s, %s, %s, %s, %s>" % (high[1], high[2], high[3], high[4], high[5], high[0])
            ardhigh.write(out.encode())
            
        except Exception as e:
            print(e)
            pass

    low = [0] * 6
    high = [0] * 6

    out = "<%s, %s, %s, %s, %s, %s>" % (low[1], low[2], low[3], low[4], low[5], low[0])
    ardlow.write(out.encode())
    
    out = "<%s, %s, %s, %s, %s, %s>" % (high[1], high[2], high[3], high[4], high[5], high[0])
    ardhigh.write(out.encode())
    
    ardlow.close()
    ardhigh.close()

#Speech

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
            print(channelnum, transcript)
            stream.is_final_end_time = stream.result_end_time
            stream.last_transcript_was_final = True

            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                stream.closed = True
                break
        else:
            stream.last_transcript_was_final = False

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
    t1 = threading.Thread(target=sep, daemon=True)
    t2 = threading.Thread(target=post, daemon=True) 
    t3 = threading.Thread(target=position, daemon=True) 
    t4 = threading.Thread(target=graph, daemon=True) 
    t5 = threading.Thread(target=arduino, daemon=True) 
    t6 = threading.Thread(target=getanalysis, daemon=True) 

    try:
        t1.start() 
        t2.start() 
        t3.start() 
        t4.start() 
        t5.start() 
        t6.start() 
    except:
        running = False
        time.sleep(0.1)
        print("\n\n\n\n\n\n\n\nEnd Thread")
        sys.exit()

    try:
        while True:
            time.sleep(1)
    except:
        running = False
        time.sleep(0.1)
        print("\n\n\n\n\n\n\n\nEnd Final")
        sys.exit()

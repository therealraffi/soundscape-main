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
    while True:
        try:
            port = 10000
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip, port))
            break
        except Exception as e:
            # print(e)
            print("Couldn't bind to that port 10000")

    def accept_connections():
        s.listen(100)

        print('Running on IP: ' + ip)
        print('Running on port: '+ str(port))
        
        while True:
            c, addr = s.accept()
            connections.append(c)
            threading.Thread(target=handle_client,args=(c,addr,)).start()
        
    def broadcast(sock, data):
        for client in connections:
            if client != s and client != sock:
                try:
                    client.send(data)
                except:
                    pass

    def handle_client(c, addr):
        global sepdata
        while True:
            try:
                sepdata = c.recv(8192)
                broadcast(c, sepdata)
                fm.append(sepdata)
            except socket.error:
                c.close()

    connections = []
    accept_connections()

def post():
    while True:
        try:
            port = 10010
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip, port))
            break
        except:
            print("Couldn't bind to that port 10010")

    def accept_connections():
        s.listen(100)

        print('Running on IP: '+ip)
        print('Running on port: '+str(port))
        
        while True:
            c, addr = s.accept()
            connections.append(c)
            threading.Thread(target=handle_client,args=(c,addr,)).start()
        
    def broadcast(sock, data):
        for client in connections:
            if client != s and client != sock:
                try:
                    client.send(data)
                except:
                    pass

    def handle_client(c, addr):
        global postdata
        while True:
            try:
                postdata = c.recv(8192)
                broadcast(c, postdata)
            except socket.error:
                c.close()

    connections = []
    accept_connections()

def position():
    # while True:
    #     try:
    #         port = 9000
    #         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         s.bind((ip, port))
    #         break
    #     except:
    #         print("Couldn't bind to that port")

    # def accept_connections():
    #     s.listen(100)

    #     print('Running on IP: ' + ip)
    #     print('Running on port: '+ str(port))
        
    #     while True:
    #         c, addr = s.accept()
    #         connections.append(c)
    #         threading.Thread(target=handle_client,args=(c,addr,)).start()
        
    # def broadcast(sock, data):
    #     for client in connections:
    #         if client != s and client != sock:
    #             try:
    #                 client.send(data)
    #             except:
    #                 pass

    # def handle_client(c, addr):
    #     global graphdata
    #     while True:
    #         try:
    #             graphdata = c.recv(8192)
    #             broadcast(c, graphdata)
    #         except socket.error:
    #             c.close()

    # connections = []
    # accept_connections()
    global graphdata
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            target_ip = "173.66.155.183"
            target_port = 9000
            s.connect((target_ip, target_port))

            break
        except:
            print("Couldn't connect to server 9000")

    while True:
        graphdata = s.recv(8192)

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

    coord = db.reference('x_and_y')   
    while True:
        try:
            coord = graphdata.decode().replace("\n", "")
            result = re.search(r'\[(.*?)]', coord).group(1)
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
            coord.set(fire)
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

        return None if math.isnan(float(out)) or len(freqdict) == 0 else max(1, int(out))

#print("%3s %6s \t %3s %6s \t %3s %6s \t %3s %6s" % (amplitude(f0[-1]), avgfreq(f0[-1]), amplitude(f1[-1]), avgfreq(f1[-1]), amplitude(f2[-1]), avgfreq(f2[-1]), amplitude(f3[-1]), avgfreq(f3[-1])), amp * "|")

def getanalysis():

    ip = '192.168.1.218'

    while True:
        try:
            port = 10050
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip, port))
            break
        except:
            print("Couldn't bind to that port 10010")

    def accept_connections():
        s.listen(100)

        print('Running on IP: '+ip)
        print('Running on port: '+str(port))
        
        while True:
            c, addr = s.accept()
            connections.append(c)
            threading.Thread(target=handle_client,args=(c,addr,)).start()
        
    def broadcast(sock, data):
        for client in connections:
            if client != s and client != sock:
                try:
                    client.send(data)
                except:
                    pass

    def handle_client(c, addr):
        global analysis
        while True:
            try:
                data = c.recv(512)
                if data != b'':
                    analysis = eval(data.decode().split("]]")[0] + "]]")
            except KeyboardInterrupt:
                c.close()
                break
            except:
                pass

    connections = []
    accept_connections()
    
def arduino():
    global sepdata
    global postdata
    global angles
    global analysis

    s = serial.Serial(port='/dev/tty.usbserial-14230', baudrate=115200)

    sound = db.reference('Sound')   

    while True:
        try:
            channels = np.frombuffer(postdata, dtype='int16')
            c0 = channels[0::8].tobytes() #red
            c1 = channels[1::8].tobytes() #green
            c2 = channels[2::8].tobytes() #blue
            c3 = channels[3::8].tobytes() #purple

            analysis = [[amplitude(c0), avgfreq(c0)], [amplitude(c1), avgfreq(c1)], [amplitude(c2), avgfreq(c2)], [amplitude(c3), avgfreq(c3)]]
            # analysis = [[sound.child("sound%s" % (i)).child("amplitude").get(), sound.child("sound%s" % (i)).child("frequency").get()] for i in range(1, 5)]
            ignore = 120

            for c in range(len(angles) - 1, -1, -1):
                i = angles[c]
                if (180 - ignore)/2 < i[0] < (180 + ignore)/2:
                    del angles[c]

            amps = [0] * 6
            inc = (360 - ignore) / 5

            possible = [(180 + ignore)/2 + i * inc for i in range(5)]
            possible.insert(0, (180 - ignore)/2)

            for angle, channel in angles:
                ind = 0
                for c, k in enumerate(possible):
                    if k - inc/2 <= angle <= k + inc/2:
                        ind = c
                        if amps[ind] != 0:
                            if ind == 5:
                                if amps[0] == 0:
                                    ind = 0
                                    break
                                if amps[4] == 0:
                                    ind = 4
                                    break
                            else:
                                if amps[ind + 1] == 0:
                                    ind += 1
                                    break
                                if amps[ind - 1] == 0:
                                    ind -= 1
                                    break
                        else:
                            break
                amps[ind] = max(analysis[channel][0] * 80/100, 0) if analysis[channel][0] > 3 else 0

            # print(angles)
            # print(analysis)
            # print(amps)
            # print("\n\n")

            out = "<%s, %s, %s, %s, %s, %s>" % (amps[0], amps[1], amps[2], amps[3], amps[4], amps[5])
            s.write(out.encode())
        except Exception as e:
            pass

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
    t1 = threading.Thread(target=sep)
    t2 = threading.Thread(target=post) 
    t3 = threading.Thread(target=position) 
    t4 = threading.Thread(target=graph) 
    t5 = threading.Thread(target=arduino) 
    t6 = threading.Thread(target=getanalysis) 

    s1 = threading.Thread(target=main, kwargs={'channelnum': 0})
    s2 = threading.Thread(target=main, kwargs={'channelnum': 1})
    s3 = threading.Thread(target=main, kwargs={'channelnum': 2})
    s4 = threading.Thread(target=main, kwargs={'channelnum': 3})

    try:
        t1.start() 
        t2.start() 
        t3.start() 
        t4.start() 
        t5.start() 
        t6.start() 

        s1.start() 
        s2.start() 
        s3.start() 
        s4.start() 

        t1.join() 
        t2.join() 
        t3.join() 
        t4.join() 
        t5.join() 
        t6.join() 

        s1.join() 
        s2.join() 
        s3.join() 
        s4.join() 
    except:
        print("\n\n\n\n\n\n\n\nEnd")
  
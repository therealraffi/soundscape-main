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
amps = [0] * 16
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
                    x = abs(math.cos(theta)) * x / abs(x)
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
            # print(angles)

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

def getamps():
    global sepdata
    global postdata
    global angles
    global analysis
    global running
    global amps

    ip = "35.186.188.127"
    # sendarduino = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # while True:
        # try:
        #     target_ip = ip
        #     target_port = 10060
        #     sendarduino.connect((target_ip, target_port))
        #     break
        # except:
        #     print("Couldn't connect to server 10060")

    while running:
        try:
            channels = np.frombuffer(sepdata, dtype='int16')
            c0 = channels[0::8].tobytes() #red
            c1 = channels[1::8].tobytes() #green
            c2 = channels[2::8].tobytes() #blue
            c3 = channels[3::8].tobytes() #purple

            analysis = [[amplitude(c0), avgfreq(c0)], [amplitude(c1), avgfreq(c1)], [amplitude(c2), avgfreq(c2)], [amplitude(c3), avgfreq(c3)]]
            #the blind sport degrees
            ignore = 90
            #number of motor pairs/group
            nummotors = 9
            #represents each motor group
            motors = [0] * nummotors
            inc = (360 - ignore) / (nummotors - 1)

            # if len(angles) != 0:
                # print(angles)

            #removes angles in blindspot
            for c in range(len(angles) - 1, -1, -1):
                i = angles[c]
                if (180 - ignore)/2 + inc/2 < i[0] < (180 + ignore)/2 - inc/2:
                    del angles[c]

            possible = [((180 + ignore)/2 + i * inc) % 360 for i in range(nummotors - 1)]
            possible.insert(0, (180 - ignore)/2)
            possible.sort()
            # print(possible)
            # print(analysis)
            for angle, channel in angles:
                ind = 0
                for c, k in enumerate(possible):
                    if k - inc/2 <= angle <= k + inc/2:
                        ind = c
                        if motors[ind] != 0:
                            if ind == nummotors - 1:
                                if motors[0] == 0:
                                    ind = 0
                                    break
                                if motors[nummotors - 2] == 0:
                                    ind = nummotors - 2
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
                #amplitude should be between 0 and 100 since arduino multiplies pwm by 2.55 - this also sets the minimum amplitude for a source to be represented
                motors[ind] = [max(analysis[channel][0] * 90/100, 0), analysis[channel][1]] if analysis[channel][0] > 2 else 0

            # print(angles)
            # print(motors)
            # print("\n\n")
            # amp = max(analysis[0][0], analysis[1][0], analysis[2][0], analysis[3][0])
            amp = amplitude(postdata)

            print("%3s %6s \t %3s %6s \t %3s %6s \t %3s %6s" % (analysis[0][0], analysis[0][1], analysis[1][0], analysis[1][1], analysis[2][0], analysis[2][1], analysis[3][0], analysis[3][1]), amp * "|")

            temp = [0] * 2 * nummotors

            for c, i in enumerate(motors):
                if i == 0:
                    temp[2 * c] = 0
                    continue
                #low freqs
                elif i[1] < 640:
                    temp[2 * c] = i[0]
                #high freqs
                else:
                    temp[2 * c + 1] = i[0]

            amps = temp
            # sendarduino.send(str(amps).encode())
            # print(amps)
            # print("\n\n")
        except Exception as e:
            print(e)
            pass

    # sendarduino.send(str(amps).encode())
    # sendarduino.close()

def sendboard():
    global amps
    teensy = serial.Serial(port='/dev/tty.usbmodem88145901', baudrate=9600)

    while running:
        try:
            out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (amps[2], amps[3], amps[0], amps[1], amps[16], amps[17], amps[14], amps[15], amps[10], amps[11], amps[8], amps[9], amps[6], amps[7], amps[4], amps[5], amps[12], amps[13])
            teensy.write(out.encode())
        except Exception as e:
            print(e)
            pass

    amps = [0] * 18

    out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    teensy.write(out.encode())

    teensy.close()

if __name__ == "__main__": 
    t1 = threading.Thread(target=sep, daemon=True)
    t2 = threading.Thread(target=post, daemon=True) 
    t3 = threading.Thread(target=position, daemon=True) 
    t4 = threading.Thread(target=graph, daemon=True) 
    t5 = threading.Thread(target=getamps, daemon=True) 
    # t6 = threading.Thread(target=getanalysis, daemon=True) 
    t7 = threading.Thread(target=sendboard, daemon=True) 

    try:
        t1.start() 
        t2.start() 
        t3.start() 
        t4.start() 
        t5.start() 
        # t6.start() 
        t7.start() 
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

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

    # ardlow = serial.Serial(port='/dev/tty.usbserial-14111340', baudrate=115200)
    # ardhigh = serial.Serial(port='/dev/tty.usbserial-14111330', baudrate=115200)

    ip = "35.186.188.127"
    sendarduino = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            target_ip = ip
            target_port = 10060
            sendarduino.connect((target_ip, target_port))
            break
        except:
            print("Couldn't connect to server 10060")

    while running:
        try:
            channels = np.frombuffer(sepdata, dtype='int16')
            c0 = channels[0::8].tobytes() #red
            c1 = channels[1::8].tobytes() #green
            c2 = channels[2::8].tobytes() #blue
            c3 = channels[3::8].tobytes() #purple

            analysis = [[amplitude(c0), avgfreq(c0)], [amplitude(c1), avgfreq(c1)], [amplitude(c2), avgfreq(c2)], [amplitude(c3), avgfreq(c3)]]
            ignore = 90
            motors = [0] * 6
            inc = (360 - ignore) / 5

            # if len(angles) != 0:
                # print(angles)
            for c in range(len(angles) - 1, -1, -1):
                i = angles[c]
                if (180 - ignore)/2 + inc/2 < i[0] < (180 + ignore)/2 - inc/2:
                    del angles[c]

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
                #amplitude should be between 0 and 100 since arduino multiplies pwm by 2.55
                motors[ind] = [max(analysis[channel][0] * 90/100, 0), analysis[channel][1]] if analysis[channel][0] > 15 else 0

            # print(analysis)
            # print(motors)
            # print("\n\n")
            # amp = max(analysis[0][0], analysis[1][0], analysis[2][0], analysis[3][0])
            amp = amplitude(postdata)

            print("%3s %6s \t %3s %6s \t %3s %6s \t %3s %6s" % (analysis[0][0], analysis[0][1], analysis[1][0], analysis[1][1], analysis[2][0], analysis[2][1], analysis[3][0], analysis[3][1]), amp * "|")

            low = [0] * 6
            high = [0] * 6
            arrarduino = [0] * 6

            for c, i in enumerate(motors):
                if i == 0:
                    arrarduino[c] = [0, 0]
                    continue
                elif i[1] > 640:
                    high[c] = i[0]
                else:
                    low[c] = i[0]
                arrarduino[c] = [low[c], high[c]]
            # print(high)
            # print(low)
            
            sendarduino.send(str(arrarduino).encode())

            # out = "<%s, %s, %s, %s, %s, %s>" % (low[1], low[2], low[3], low[4], low[5], low[0])
            # ardlow.write(out.encode())
            
            # out = "<%s, %s, %s, %s, %s, %s>" % (high[1], high[2], high[3], high[4], high[5], high[0])
            # ardhigh.write(out.encode())
            
        except Exception as e:
            print(e)
            pass

    low = [0] * 6
    high = [0] * 6
    arduino = [0] * 6

    out = "<%s, %s, %s, %s, %s, %s>" % (low[1], low[2], low[3], low[4], low[5], low[0])
    # ardlow.write(out.encode())
    
    out = "<%s, %s, %s, %s, %s, %s>" % (high[1], high[2], high[3], high[4], high[5], high[0])
    # ardhigh.write(out.encode())

    sendarduino.send(str(arduino).encode())
    
    # ardlow.close()
    # ardhigh.close()
    sendarduino.close()

#Speech

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

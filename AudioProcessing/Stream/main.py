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

#Local IP
ip = socket.gethostbyname(socket.gethostname())

#Firebase
cred = credentials.Certificate('soundy-8d98a-firebase-adminsdk-o03jf-c7fede8ea2.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})

#Global Data Vars
graphdata = ""
postdata = ""

def sep():
    while True:
        try:
            port = 10000
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip, port))
            break
        except:
            print("Couldn't bind to that port")

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
        while True:
            try:
                data = c.recv(8192)
                broadcast(c, data)
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
            print("Couldn't bind to that port")

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
    global graphdata
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            target_ip = "192.168.1.218"
            target_port = 9000
            s.connect((target_ip, target_port))

            break
        except:
            print("Couldn't connect to server")

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
    ref = db.reference('x_and_y')   
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
            for i in range(len(points)):
                angle = math.atan2(points[i][1], points[i][0]) * 180 / math.pi + 60
                if angle < 0:
                    angle += 360
                angle *= math.pi/180
                plot.append([math.cos(angle), math.sin(angle)])
                
            fire = eval(firejson(plot, ind))
            ref.set(fire)

def sig(num):
    return 1/(1 + math.exp(-10 * num))

def amplitude(block):
    count = len(block)/2
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
        result = np.fromstring(block, dtype=np.int16)
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

        print()
        for i in freqdict:
            print(int(i), "\t", freqdict[i] * 100 / wsum)
        print()

        out = 0
        for i in freqdict:
            out += i * freqdict[i] / wsum

        return None if math.isnan(float(out)) or len(freqdict) == 0 else max(1, int(out))

def ardunio():
    pass

if __name__ == "__main__": 
    t1 = threading.Thread(target=sep) 
    t2 = threading.Thread(target=post) 
    t3 = threading.Thread(target=position) 
    t4 = threading.Thread(target=graph) 
    t5 = threading.Thread(target=arduino) 

    t1.start() 
    t2.start() 
    t3.start() 
    t4.start() 
    t5.start() 
  
    t1.join() 
    t2.join() 
    t3.join() 
    t4.join() 
    t5.join() 
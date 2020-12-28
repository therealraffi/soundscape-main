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
graphdata = b""
sepdata = b""
postdata = b""
angles = []
analysis = []

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
            ref.set(fire)
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
    global angles
    global analysis

    s = serial.Serial(port='/dev/tty.usbserial-14230', baudrate=115200)

    sound = db.reference('Sound')   

    while True:
        try:
            channels = np.frombuffer(sepdata, dtype='int16')
            c0 = channels[0::8].tobytes() #red
            c1 = channels[1::8].tobytes() #green
            c2 = channels[2::8].tobytes() #blue
            c3 = channels[3::8].tobytes() #purple

            # analysis = [[amplitude(c0), avgfreq(c0)], [amplitude(c1), avgfreq(c1)], [amplitude(c2), avgfreq(c2)], [amplitude(c3), avgfreq(c3)]]
            # analysis = [[sound.child("sound%s" % (i)).child("amplitude").get(), sound.child("sound%s" % (i)).child("frequency").get()] for i in range(1, 5)]
            ignore = 120

            for c in range(len(angles) - 1, -1, -1):
                i = angles[c]
                if (180 - ignore)/2 < i[0] < (180 + ignore)/2:
                    print(i)
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
                amps[ind] = max(analysis[channel][0], 1)

            print(angles)
            print(analysis)
            print(amps)
            print("\n\n")

            out = "<%s, %s, %s, %s, %s, %s>" % (amps[0], amps[1], amps[2], amps[3], amps[4], amps[5])
            s.write(out.encode())
        except Exception as e:
            pass

if __name__ == "__main__": 
    t1 = threading.Thread(target=sep)
    t2 = threading.Thread(target=post) 
    t3 = threading.Thread(target=position) 
    t4 = threading.Thread(target=graph) 
    t5 = threading.Thread(target=arduino) 
    t6 = threading.Thread(target=getanalysis) 

    try:
        t1.start() 
        t2.start() 
        t3.start() 
        t4.start() 
        t5.start() 
        t6.start() 

        t1.join() 
        t2.join() 
        t3.join() 
        t4.join() 
        t5.join() 
        t6.join() 
    except:
        print("\n\n\n\n\n\n\n\nEnd")
  
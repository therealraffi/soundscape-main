import socket
import threading
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
from pixel_ring import pixel_ring
from gpiozero import LED
import serial

#global
graphdata = b''

#broadcast
def data():
    ip = socket.gethostbyname(socket.gethostname())
    ip = "192.168.1.233"

    while True:
        try:
            port = 9000
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

    def handle_client(cin, addr):
        global graphdata
        while True:
            try:
                graphdata = cin.recv(8192)
                broadcast(cin, graphdata)
            except:
                pass

    connections = []
    accept_connections()


#plt
'''
plt.axis([-1.1, 1.1, -1.1, 1.1])
ax = plt.gca()
ax.spines['top'].set_color('none')
ax.spines['bottom'].set_position('zero')
ax.spines['left'].set_position('zero')
ax.spines['right'].set_color('none')
ax.add_artist(plt.Circle((0, 0), 1, color='k', fill=False))
ax.set_aspect("equal")
'''

def graph():
    global graphdata

    #pixel ring
    power = LED(5)
    power.on()
    pixel_ring.set_brightness(20)
    pixel_ring.change_pattern('custom')
    
    while True:
        try:
            coord = graphdata.decode().replace("\n", "").split("}\n{")[0]
            coord = json.loads(coord)["src"]

            points = []
            plot = []
            ind = []
            colors = ["r", "g", "b", "m"]

            for c, i in enumerate(coord):
                x = i["x"]
                y = i["y"]
                z = i["z"]
                if x != 0 and y != 0 and z != 0:
                    theta = math.atan(y/x)
                    x_f = abs(math.cos(theta)) * x / abs(x) * -1
                    y_f = abs(math.sin(theta)) * y / abs(y) * -1
                    points.append([x_f, y_f])

                    '''
                    theta += math.pi/6
                    x_f = abs(math.cos(theta)) * x / abs(x) * -1
                    y_f = abs(math.sin(theta)) * y / abs(y) * -1
                    plot.append([x_f, -1 * y_f, theta])
                    '''

                    ind.append(colors[c])

            points = np.array(points)
#            plot = np.array(plot)

            ledstr = ""
            for i in range(len(points)):
                angle = math.atan2(points[i][1], points[i][0]) * 180 / math.pi
                if angle < 0:
                    angle += 360
                ledstr += str(int(angle//30) % 12) + " " + ind[i] + "-"

            pixel_ring.wakeup(ledstr)

            #Graph
            '''
            print(plot)
            points = plt.scatter(plot[:, 0], plot[:, 1], c=ind, s = 50)
            plt.pause(0.000001)
            points.remove()
            '''
            # pixel_ring.off()
        except KeyboardInterrupt as e:
            return
        except Exception as e:
            pass



if __name__ == "__main__": 
    t1 = threading.Thread(target=data)
    t2 = threading.Thread(target=graph) 

    try:
        t1.start() 
        t2.start() 

        t1.join() 
        t2.join() 
    except:
        print("\n\nEnd")
  
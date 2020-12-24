import socket
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import re
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate('soundy-8d98a-firebase-adminsdk-o03jf-c7fede8ea2.json')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})
ref = db.reference('x_and_y')

while True:
    try:
        target_ip = "173.66.155.183"
        target_port = 9000
        s.connect((target_ip, target_port))

        break
    except:
        print("Couldn't connect to server")

#plt
plt.axis([-1.1, 1.1, -1.1, 1.1])
ax = plt.gca()
ax.spines['top'].set_color('none')
ax.spines['bottom'].set_position('zero')
ax.spines['left'].set_position('zero')
ax.spines['right'].set_color('none')
ax.add_artist(plt.Circle((0, 0), 1, color='b', fill=False))
ax.set_aspect("equal")

while True:
    data = s.recv(8192)
    coord = data.decode().replace("\n", "")
    try:
        result = re.search(r'\[(.*?)]', coord).group(1)
        xc = re.findall(r'"x": (.*?),', result)
        yc = re.findall(r'"y": (.*?),', result)
        zc = re.findall(r'"z": (.*?),', result)
        points = []
        ind = []
        colors = ["r", "g", "b", "m"]

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
            
        plot = np.array(plot)
        plot = plt.scatter(plot[:, 0], plot[:, 1], c=ind, s = 50)
        plt.pause(0.00001)
        plot.remove()
    except KeyboardInterrupt as e:
        break
    except Exception as e:
        pass

plt.show()

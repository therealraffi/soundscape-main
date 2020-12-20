import socket
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
import re

#tcp stuff
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('192.168.1.218', 9000)
sock.bind(server_address)
sock.listen(1)
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
    connection, client_address = sock.accept()
    try:
        while True:
            data = connection.recv(8192)
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
                        x_f = abs(math.cos(theta)) * x / abs(x)
                        y_f = abs(math.sin(theta)) * y / abs(y)
                        points.append([x_f, y_f])
                        ind.append(colors[i])
                points = np.array(points)
                # print(points)
                # print(coord)
                points = plt.scatter(points[:, 0], points[:, 1], c=ind, s = 50)
                plt.pause(0.00001)
                points.remove()
                # print("\n")
            except Exception as e:
                print(e)
                pass
            if data:
                pass
            else:
                print('no more data from')
                break
    finally:
        connection.close()
plt.show()

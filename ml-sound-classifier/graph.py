import socket
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt
from time import sleep
from pixel_ring import pixel_ring
from gpiozero import LED
import serial

#pixel ring
power = LED(5)
power.on()
pixel_ring.set_brightness(20)
pixel_ring.change_pattern('custom')

#tcp stuff
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('127.0.0.1', 9000)
sock.bind(server_address)
sock.listen(1)

#serial
'''
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.flush()
'''
motors = [0, 0, 0, 0, 0, 0]


#plt
plt.axis([-1.1, 1.1, -1.1, 1.1])
ax = plt.gca()
ax.spines['top'].set_color('none')
ax.spines['bottom'].set_position('zero')
ax.spines['left'].set_position('zero')
ax.spines['right'].set_color('none')
ax.add_artist(plt.Circle((0, 0), 1, color='k', fill=False))
ax.set_aspect("equal")

while True:
    connection, client_address = sock.accept()
    try:
        while True:
            data = connection.recv(4096)
            coord = data.decode().replace("\n", "").split("}\n{")[0]
            try:
                coord = json.loads(coord)["src"]
                points = []
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
                        ind.append(colors[c])
                points = np.array(points)
                ledstr = ""
                for i in range(len(points)):
                    angle = math.atan2(points[i][1], points[i][0]) * 180 / math.pi
                    if angle < 0:
                        angle += 360
                    ledstr += str(int(angle//30) % 12) + " " + ind[i] + "-"
                    motors[int(angle//60) % 6] = 1

                out = "<" + str(motors[0]) + ", " + str(motors[1]) + ">"
#                ser.write(out.encode())
                pixel_ring.wakeup(ledstr)
#                print(ledstr)
#                print(points)
#                print(coord)
#                points = plt.scatter(points[:, 0], points[:, 1], c=ind, s = 50)
#                plt.pause(0.000001)
#                points.remove()
#                print("\n")
#                pixel_ring.off()
            except Exception as e:
                motors[0] = 0
                motors[1] = 0
                out = "<" + str(motors[0]) + ", " + str(motors[1]) + ">"
#                ser.write(out.encode())
#                connection.close()
#                print(e)
                pass
            if data:
                pass
            else:
                print('no more data from')
                break
    finally:
        connection.close()

#plt.show()

# import socket               # Import socket module

# arr = [[13, 21], [42, 2], [23, 41], [1, 2]]

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# a.connect(('173.66.155.183', 10050))
# a.sendall((str(arr)).encode())
# a.close()

import socket  
import threading
import time

ip = "173.66.155.183"
arr = [[13, 21], [42, 2], [23, 41], [1, 2]]
a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while True:
    try:
        target_ip = ip
        target_port = 10050
        a.connect((target_ip, target_port))
        break
    except:
        print("Couldn't connect to server")

while True:
    try:
        data = a.send((str(arr)).encode())
        arr[0][1] += 1
        time.sleep(0.001)
    except KeyboardInterrupt:
        a.close()
        break
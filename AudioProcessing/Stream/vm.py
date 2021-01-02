import socket
import threading
import numpy as np
import re
import math
import struct
import time
import sys

#Local IP
ip = socket.gethostbyname(socket.gethostname())
counts = {}
data = {}

def stream(port):
    global ip
    global counts
    global data 
    counts[port] = 0
    data[port] = b""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #Open up local port
            s.bind((ip, port))
            break
        except Exception as e:
            # print(e)
            print("Couldn't bind to that port %s" % (port))

    def accept_connections():
        s.listen(100)
        print('Running on IP: ' + ip)
        print('Running on port: '+ str(port))
        
        while True:
            try:
                c, addr = s.accept()
                connections.append(c)
                threading.Thread(target=handle_client, args=(c, addr, counts[port])).start()
            except KeyboardInterrupt:
                c.close()
        
    def broadcast(sock, data):
        for client in connections:
            if client != s and client != sock:
                try:
                    client.send(data)
                except:
                    pass

    def handle_client(c, addr, counter):
        counts[port] += 1
        while True:
            try:
                if counter == 0:
                    data[port] = c.recv(8192)
                broadcast(c, data[port])
            except socket.error:
                c.close()
            except KeyboardInterrupt:
                c.close()
    connections = []
    accept_connections()

if __name__ == "__main__": 
    t1 = threading.Thread(target=stream, kwargs={'port': 9000}, daemon=True)
    t2 = threading.Thread(target=stream, kwargs={'port': 10000}, daemon=True)
    t3 = threading.Thread(target=stream, kwargs={'port': 10010}, daemon=True)
    t4 = threading.Thread(target=stream, kwargs={'port': 10050}, daemon=True)

    t1.start() 
    t2.start() 
    t3.start() 
    t4.start() 
    try:
        while True:
            time.sleep(1)
    except:
        print("\n\n\n\n\n\n\n\nEnd")
        sys.exit()
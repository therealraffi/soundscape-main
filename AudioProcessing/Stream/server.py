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
running = True

def stream(port):
    global ip
    global counts
    global data 
    global running

    counts[port] = 0
    data[port] = b""
    while running:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #Open up local port
            s.bind((ip, port))
            break
        except Exception as e:
            # print(e)
            print("Couldn't bind to that port %s" % (port))
            
    def accept_connections():
        global running
        s.listen(100)
        print('Running on IP: ' + ip)
        print('Running on port: '+ str(port))
        
        while running:
            try:
                c, addr = s.accept()
                connections.append(c)
                threading.Thread(target=handle_client, args=(c, addr, counts[port])).start()
            except KeyboardInterrupt:
                c.close()
        c.close()
        
    def broadcast(sock, data):
        for client in connections:
            if client != s and client != sock:
                try:
                    client.send(data)
                except:
                    pass

    def handle_client(c, addr, counter):
        global running
        counts[port] += 1
        while running:
            try:
                if counter == 0:
                    data[port] = c.recv(8192)
                broadcast(c, data[port])
            except socket.error:
                c.close()
            except KeyboardInterrupt:
                c.close()
        c.close()

    connections = []
    accept_connections()

if __name__ == "__main__": 
    #Sound localization coordinates
    t1 = threading.Thread(target=stream, kwargs={'port': 9000}, daemon=True)
    #Separated Audio Streams
    t2 = threading.Thread(target=stream, kwargs={'port': 10000}, daemon=True)
    #Postfiltered Separated Audio Streams
    t3 = threading.Thread(target=stream, kwargs={'port': 10010}, daemon=True)
    #Noise filtered amplitudes and frequencies - analysis 
    t4 = threading.Thread(target=stream, kwargs={'port': 10050}, daemon=True)
    #Computer looks through analysis and determines arduino port array - send to pi
    t5 = threading.Thread(target=stream, kwargs={'port': 10060}, daemon=True)
    t1.start() 
    t2.start() 
    t3.start() 
    t4.start() 
    t5.start()
    try:
        while True:
            time.sleep(1)
    except:
        running = False
        print("\n\n\n\n\n\n\n\nEnd")
        time.sleep(0.1)
        sys.exit()
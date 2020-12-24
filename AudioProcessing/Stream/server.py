import socket
import threading
import pyaudio
import numpy as np

ip = socket.gethostbyname(socket.gethostname())

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
    while True:
        try:
            data = c.recv(8192)
            broadcast(c, data)
        
        except socket.error:
            c.close()

connections = []
accept_connections()
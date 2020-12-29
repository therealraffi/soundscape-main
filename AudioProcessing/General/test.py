import socket  
import threading

ip = '192.168.1.218'

while True:
    try:
        port = 10050
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((ip, port))
        break
    except:
        print("Couldn't bind to that port 10050")

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
            if data != b'':
                analysis = eval(data.decode().split("]]")[0] + "]]")
                print(analysis)
        except socket.error:
            c.close()
        except KeyboardInterrupt:
            c.close()
            break

connections = []
accept_connections()
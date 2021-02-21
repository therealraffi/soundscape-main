import serial
import socket
import re
import threading
import time
import sys

arduino = []
running = True

def getanalysis():
    global arduino
    global running
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            target_ip = "35.186.188.127"
            target_port = 10060
            s.connect((target_ip, target_port))
            break
        except:
            print("Couldn't connect to server 10060")

    while running:
        try:
            data = s.recv(512)
            if data != b'':
                arduino = eval("[[" + re.findall(r'\[\[(.*?)\]\]', data.decode())[0] + "]]")
            # time.sleep(0.01)
        except Exception as e:
            # print(e)
            pass
    s.close()

def setarduino():
    global arduino
    global running

    teensy = serial.Serial(port='/dev/ttyUSB0', baudrate=115200)

    while running:
        try:
            amps = [0] * 16

            for c, i in enumerate(arduino):
#                if c != 2:
#                    continue
                amps[c] = i

            print(amps)
            print()

            out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (amps[1], amps[2], amps[3], amps[4], amps[5], amps[6], amps[7], amps[8], amps[9], amps[10], amps[11], amps[12], amps[13], amps[14], amps[15], amps[0])
            teensy.write(out.encode())
            
        except Exception as e:
            print(e)
            pass

    amps = [0] * 16

    out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (amps[1], amps[2], amps[3], amps[4], amps[5], amps[6], amps[7], amps[8], amps[9], amps[10], amps[11], amps[12], amps[13], amps[14], amps[15], amps[0])

    teensy.write(out.encode())
    teensy.close()

if __name__ == "__main__": 
    t1 = threading.Thread(target=setarduino, daemon=True) 
    t2 = threading.Thread(target=getanalysis, daemon=True) 

    try:
        t1.start() 
        t2.start() 
    except:
        running = False
        time.sleep(0.1)
        print("\n\n\n\n\n\n\n\nEnd Thread")
        sys.exit()

    try:
        while True:
            time.sleep(1)
    except:
        running = False
        time.sleep(0.1)
        print("\n\n\n\n\n\n\n\nEnd Final")
        sys.exit()
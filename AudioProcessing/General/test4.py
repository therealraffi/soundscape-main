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

    ardlow = serial.Serial(port='/dev/tty.usbserial-14111340', baudrate=115200)
    ardhigh = serial.Serial(port='/dev/tty.usbserial-14111330', baudrate=115200)

    while running:
        try:

            low = [0] * 6
            high = [0] * 6

            for c, i in enumerate(arduino):
                low[c] = i[0]
                high[c] = i[1]

            # print(arduino)
            print(low)
            print(high)
            print()

            out = "<%s, %s, %s, %s, %s, %s>" % (low[1], low[2], low[3], low[4], low[5], low[0])
            ardlow.write(out.encode())
            
            out = "<%s, %s, %s, %s, %s, %s>" % (high[1], high[2], high[3], high[4], high[5], high[0])
            ardhigh.write(out.encode())
            
        except Exception as e:
            print(e)
            pass

    low = [0] * 6
    high = [0] * 6

    out = "<%s, %s, %s, %s, %s, %s>" % (low[1], low[2], low[3], low[4], low[5], low[0])
    ardlow.write(out.encode())
    
    out = "<%s, %s, %s, %s, %s, %s>" % (high[1], high[2], high[3], high[4], high[5], high[0])
    ardhigh.write(out.encode())
    
    ardlow.close()
    ardhigh.close()

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

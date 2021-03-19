import serial

def sendboard():
    teensy = serial.Serial(port='/dev/ttyACM0', baudrate=9600)
    amps = [10] * 18
    while True:
        try:
            out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (amps[2], amps[3], amps[0], amps[1], amps[16], amps[17], amps[14], amps[15], amps[10], amps[11], amps[8], amps[9], amps[6], amps[7], amps[4], amps[5], amps[12], amps[13])
            teensy.write(out.encode())
        except Exception as e:    
            amps = [0] * 18
            out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            teensy.write(out.encode())
            teensy.close()
            print(e)
            pass

    amps = [0] * 18

    out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    teensy.write(out.encode())

    teensy.close()

sendboard()
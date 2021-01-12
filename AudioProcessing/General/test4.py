import serial

ardlow = serial.Serial(port='/dev/tty.usbserial-14111340', baudrate=115200)
ardhigh = serial.Serial(port='/dev/tty.usbserial-14111330', baudrate=115200)

low = [70, 70, 70, 70, 70, 70]
high = [10, 90, 70, 10, 70, 10]


while True:
    out = "<%s, %s, %s, %s, %s, %s>" % (low[0], low[1], low[2], low[3], low[4], low[5])
    ardlow.write(out.encode())

    # out = "<%s, %s, %s, %s, %s, %s>" % (high[0], high[1], high[2], high[3], high[4], high[5])
    # ardhigh.write(out.encode())
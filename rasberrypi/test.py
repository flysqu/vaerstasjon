import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"{port.device}: {port.description}")


# Port on rasberry pi is called "/dev/ttyACM0". 
# For testing it is set here to the windows value COM3
ser = serial.Serial('COM5', 9600, timeout=1)

# Send data
while True:
        data = ser.readline()
        print(data)
        data = data.decode('utf-8')
        data_s = data.rstrip().split(' ')
        print(data_s)
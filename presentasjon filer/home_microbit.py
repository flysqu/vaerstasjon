from microbit import *
from machine import *
import radio

radio.config(group=60,length=32)
radio.on()

# Funksjon som verifiserer om all data ligger der
def verify_data(data):
    # data is a list of payload-like fragments (e.g. 'W...', ':T...', ':H...')
    data = str(data)
    data.split(":")
    if not data:
        print("verify_data: empty")
        return False

    # This is what the data is supposed to look like
    # send_string = "W"+str(speed)+":D"+str(direction)+":R"+str(rainfall)+":T"+str(temp)
    parts = data.split(":")
    print(parts)
    if len(parts) != 4:
        print("verify_data: incorrect number of parts")
        return False
    if not (parts[0].startswith("W") and parts[0][1:].isdigit()):
        print("verify_data: invalid W part")
        return False
    if not (parts[1].startswith("D") and parts[1][1:].isdigit()):
        print("verify_data: invalid D part")
        return False
    if not (parts[2].startswith("R") and parts[2][1:].isdigit()):
        print("verify_data: invalid R part")
        return False
    if not (parts[3].startswith("T") and parts[3][1:].isdigit()):
        print("verify_data: invalid T part")
        return False

    return True

def output_data(data):
    print(data)

def run():
    UART = uart.init(baudrate=9600)
    while True:
        message = radio.receive()
        if not message:
            sleep(50)
            continue

        if message and verify_data(message):
            output_data(message)
            

print("Starting...")
display.show('S')
run()


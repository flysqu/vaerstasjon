from microbit import *
from machine import *
import radio

radio.config(group=60,length=32)
radio.on()

# Funksjon som verifiserer om all data ligger der
def verify_data(data):
    # Accept a raw payload string or list of fragments.
    if isinstance(data, list):
        data = "".join(data)
    if not data:
        print("verify_data: empty")
        return False

    data = str(data).strip()
    if not data.startswith("W"):
        print("verify_data: missing W prefix")
        return False

    parts = data.split(":")
    if len(parts) < 4 or len(parts) > 6:
        print("verify_data: incorrect number of parts")
        return False

    if not (parts[0].startswith("W") and parts[0][1:].isdigit()):
        print("verify_data: invalid W part - "+parts[0])
        return False
    if len(parts) < 2 or not (parts[1].startswith("D")):
        print("verify_data: invalid D part - "+parts[1])
        return False
    if len(parts) < 3 or not (parts[2].startswith("R") and parts[2][1:].isdigit()):
        print("verify_data: invalid R part - "+parts[2])
        return False
    if len(parts) < 4 or not parts[3].startswith("T"):
        print("verify_data: invalid T part - "+parts[3])
        return False

    temp_part = parts[3][1:]
    if not temp_part or not all(c.isdigit() or c == '.' or c == '-' for c in temp_part):
        print("verify_data: invalid T value - "+temp_part)
        return False

    if len(parts) >= 5:
        if not parts[4].startswith("P"):
            print("verify_data: invalid P part - "+parts[4])
            return False
        pressure_part = parts[4][1:]
        if not pressure_part or not all(c.isdigit() or c == '.' or c == '-' for c in pressure_part):
            print("verify_data: invalid P value - "+pressure_part)
            return False

    if len(parts) == 6:
        
        if not parts[5].startswith("H"):
            print("verify_data: invalid H part - "+parts[5])
            print(parts)
            return False
        humidity_part = parts[5][1:]
        if not humidity_part or not humidity_part.isdigit():
            print("verify_data: invalid H value - "+parts[5])
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


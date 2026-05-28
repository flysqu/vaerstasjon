from microbit import *
from machine import *
import radio

radio.config(group=60,length=32)
radio.on()

def verify_data(data):
    # data is a list of payload-like fragments (e.g. 'W...', ':T...', ':H...')
    if not data:
        print("verify_data: empty")
        return False

    parts = [p for p in data if p and p != 'START' and p != 'END']
    if not parts:
        print("verify_data: no payload parts")
        return False

    # Find the last W fragment and ensure T and H follow it
    w_idx = None
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].startswith("W"):
            w_idx = i
            break

    if w_idx is None:
        print("verify_data: missing W fragment")
        return False
    if w_idx + 2 >= len(parts):
        print("verify_data: incomplete payload after W")
        return False

    w_frag = parts[w_idx]
    t_frag = parts[w_idx + 1]
    h_frag = parts[w_idx + 2]

    if not (w_frag.startswith("W") and ":D" in w_frag and ":R" in w_frag):
        print("verify_data: bad W fragment")
        return False
    if not (t_frag.startswith(":T") and ":P" in t_frag):
        print("verify_data: bad T fragment")
        return False
    if not (h_frag.startswith(":H") and ":A" in h_frag):
        print("verify_data: bad H fragment")
        return False

    return True

def output_data(data):
    print(data)
    
def run():
    #UART = uart.init(baudrate=9600)
    recived_strings = []
    while True:
        message = radio.receive()
        if not message:
            sleep(50)
            continue

        if message == "START":
            # Collect fragments until we get END. Ignore repeated STARTs and unexpected fragments.
            recived_strings = []
            while True:
                m = radio.receive()
                if not m:
                    sleep(50)
                    continue
                if m == "END":
                    break
                if m == "START":
                    # Transmission restarted; discard what we've collected so far
                    recived_strings = []
                    continue
                # Only accept the expected payload fragments
                if m.startswith("W") or m.startswith(":T") or m.startswith(":H"):
                    recived_strings.append(m)
                # otherwise ignore noise or leftover markers

            print("Collected fragments:", recived_strings)

            if verify_data(recived_strings):
                radio.send("1")
                print("Verified!")
                # extract the last complete W/T/H set and output that
                parts = [p for p in recived_strings if p]
                w_idx = None
                for i in range(len(parts) - 1, -1, -1):
                    if parts[i].startswith("W"):
                        w_idx = i
                        break
                if w_idx is not None and w_idx + 2 < len(parts):
                    payload = [parts[w_idx], parts[w_idx + 1], parts[w_idx + 2]]
                else:
                    payload = parts
                output_data(payload)
                recived_strings = []
            else:
                radio.send("0")
                recived_strings = []
            

print("Starting...")
display.show('S')
run()


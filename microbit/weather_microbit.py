from microbit import *
import bme280_microbit_lowmem as bme280
import utime
import radio
radio.config(group=60,length=32)
radio.on()

# Global variables
num_rain_dumps = 0
rain_monitor_started = False
last_pin_state = 1  # Start assuming HIGH (due to pull-up)
num_wind_turns = 0
wind_mph = 0.0
wind_monitor_started = False
last_wind_pin_state = 1
last_wind_update_time = 0

def wind_direction():
    """
    Read the wind direction from the wind vane on pin P1.
    Returns a string representing the direction (N, E, S, W, NE, NW, SE, SW).
    """
    start_wind_monitoring()
    
    # Read analog value from P1 (0-1023 range)
    wind_dir = pin1.read_analog()
    
    # Check direction based on voltage ranges
    if 886 < wind_dir < 906:
        return "N"
    elif 692 < wind_dir < 712:
        return "NE"
    elif 395 < wind_dir < 415:
        return "E"
    elif 478 < wind_dir < 498:
        return "SE"
    elif 564 < wind_dir < 584:
        return "S"
    elif 799 < wind_dir < 819:
        return "SW"
    elif 968 < wind_dir < 988:
        return "W"
    elif 939 < wind_dir < 959:
        return "NW"
    else:
        return "???"

def wind_speed():
    """
    Read the instantaneous wind speed from the anemometer in MPH.
    Must call update_wind_speed() regularly for accurate readings.
    
    Returns:
        float: Wind speed in miles per hour
    """
    start_wind_monitoring()
    return wind_mph

def check_wind_pulse():
    """
    Checks for a rising edge on P8 (anemometer rotation).
    Must be called regularly in your main loop.
    Increments wind turn counter when pulse detected.
    """
    global num_wind_turns, last_wind_pin_state
    
    current_state = pin8.read_digital()
    
    # Detect rising edge: was LOW (0), now HIGH (1)
    if last_wind_pin_state == 0 and current_state == 1:
        num_wind_turns += 1
    
    last_wind_pin_state = current_state

def update_wind_speed():
    """
    Updates the wind speed calculation based on rotations counted.
    Should be called every 2 seconds for accurate MPH readings.
    Automatically resets the rotation counter.
    """
    global wind_mph, num_wind_turns, last_wind_update_time
    
    current_time = running_time()
    
    # Only update if 2 seconds have passed
    if current_time - last_wind_update_time >= 2000:
        # Calculate MPH: (rotations / 2 seconds) / (1492 / 1000)
        # Simplified: rotations / 2.984
        wind_mph = (num_wind_turns / 2) / 1.492
        num_wind_turns = 0
        last_wind_update_time = current_time

def start_wind_monitoring():
    """
    Sets up pin 8 to monitor anemometer pulses.
    Configures pull-up resistor for the wind sensor.
    """
    global wind_monitor_started, last_wind_pin_state, last_wind_update_time
    
    # Only initialize once
    if wind_monitor_started:
        return
    
    # Configure P8 with pull-up resistor
    pin8.set_pull(pin8.PULL_UP)
    last_wind_pin_state = pin8.read_digital()
    last_wind_update_time = running_time()
    
    wind_monitor_started = True

def check_rain_pulse():
    """
    Checks for a rising edge on P2 (LOW to HIGH transition).
    Must be called regularly in your main loop.
    Increments rain dump counter when pulse detected.
    """
    global num_rain_dumps, last_pin_state
    
    current_state = pin2.read_digital()
    
    # Detect rising edge: was LOW (0), now HIGH (1)
    if last_pin_state == 0 and current_state == 1:
        num_rain_dumps += 1
    
    last_pin_state = current_state

def start_rain_monitoring():
    """
    Sets up pin 2 to monitor rain gauge pulses.
    Configures pull-up resistor for the rain sensor.
    """
    global rain_monitor_started, last_pin_state
    
    # Only initialize once
    if rain_monitor_started:
        return
    
    # Configure P2 with pull-up resistor
    # This keeps the pin HIGH normally, sensor pulls it LOW when triggered
    pin2.set_pull(pin2.PULL_UP)
    last_pin_state = pin2.read_digital()
    
    rain_monitor_started = True

def rain_cm():
    """
    Returns the amount of rain in centimeters.
    Each dump of the rain gauge = 0.011 inches

    Returns:
        float: Centimeters of rain measured
    """
    start_rain_monitoring()

    # inches: dumps * 0.011
    inches_of_rain = (num_rain_dumps * 11) / 1000.0
    cm_of_rain = inches_of_rain * 2.54
    return cm_of_rain

async def _send_all(direction,speed,temp,pressure,humidity,altitude,rainfall):
    send_string = "W"+str(speed)+"D"+str(direction)+"T"+str(temp)+"P"+str(pressure)+"H"+str(humidity)+"A"+str(altitude)+"R"+str(rainfall)
    print(len(send_string))

def reset_rain():
    """
    Optional helper function to reset the rain counter.
    """
    global num_rain_dumps
    num_rain_dumps = 0

bme = bme280.BME280(i2c, address=0x76)
    
start_rain_monitoring()
start_wind_monitoring()

FAST_INTERVAL = 75

# Send main telemetry every 15 minutes
#RADIO_INTERVAL = 15 * 60 * 1000  # 15 minutes in milliseconds
RADIO_INTERVAL = 5000

SLOW_INTERVAL = 2000

last_fast = utime.ticks_ms()
last_radio = utime.ticks_ms()
last_slow = utime.ticks_ms()

while True:
    now = utime.ticks_ms()

    if utime.ticks_diff(now, last_fast) >= FAST_INTERVAL:
        display.show(Image.BUTTERFLY)
        
        last_fast = utime.ticks_add(last_fast, FAST_INTERVAL)
        
        check_rain_pulse()
        check_wind_pulse()
    if utime.ticks_diff(now, last_radio) >= RADIO_INTERVAL:
        last_radio = utime.ticks_add(last_radio, RADIO_INTERVAL)
        
        direction = wind_direction()
        speed = wind_speed()
        temp, pressure, humidity = bme.values()
        altitude = bme.altitude()
        rainfall = rain_cm()
        
        send_strings = ["START","W"+str(speed)+":D"+str(direction)+":R"+str(rainfall),":T"+str(temp)+":P"+str(pressure),":H"+str(humidity)+":A"+str(altitude),"END"]
        display.show(Image.HAPPY)
        for send_string in send_strings:
            #print("Lenght of '"+send_string+"' is "+str(len(send_string)))
            radio.send(send_string)
            print("Sent original string")

            sleep(100)

        # Radio signals are often unreliable and may be corrupted
        # Use a bounded retry with timeout to avoid infinite waiting
        print("Checking for ACK (will timeout and retry)")
        MAX_RETRIES = 3
        ACK_TIMEOUT_MS = 5000  # wait up to 5 seconds per attempt
        success = False
        attempt = 0
        while attempt < MAX_RETRIES and not success:
            attempt += 1
            print("Waiting for ACK (attempt " + str(attempt) + "/" + str(MAX_RETRIES) + ")")
            start = utime.ticks_ms()
            while utime.ticks_diff(utime.ticks_ms(), start) < ACK_TIMEOUT_MS:
                msg = radio.receive()
                if msg:
                    if msg == "1":
                        print("String was received correctly")
                        success = True
                        break
                    elif msg == "0":
                        print("Receiver reported corrupted data")
                        break
                sleep(100)

            if not success and attempt < MAX_RETRIES:
                print("Resending payload (retry " + str(attempt) + ")")
                for s in send_strings:
                    radio.send(s)
                    sleep(100)
                sleep(200)

        if not success:
            print("No ACK received after " + str(MAX_RETRIES) + " attempts, giving up.")


        # Reset rainfall counter so next interval reports per-interval rainfall
        reset_rain()
    if utime.ticks_diff(now, last_slow) >= SLOW_INTERVAL:
        display.show(Image.ARROW_E)
        last_slow = utime.ticks_add(last_slow, SLOW_INTERVAL)
        
        update_wind_speed()


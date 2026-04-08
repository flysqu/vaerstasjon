from microbit import *
import bme280_microbit_lowmem as bme280
import utime
import radio
import værstasjon_micropython
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

bme = bme280.BME280(i2c, address=0x76)
    
værstasjon_micropython.start_rain_monitoring()
værstasjon_micropython.start_wind_monitoring()

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
        
        værstasjon_micropython.check_rain_pulse()
        værstasjon_micropython.check_wind_pulse()
    if utime.ticks_diff(now, last_radio) >= RADIO_INTERVAL:
        last_radio = utime.ticks_add(last_radio, RADIO_INTERVAL)
        
        direction = værstasjon_micropython.wind_direction()
        speed = værstasjon_micropython.wind_speed()
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
        
        værstasjon_micropython.update_wind_speed()


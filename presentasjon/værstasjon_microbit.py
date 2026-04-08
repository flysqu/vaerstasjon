from microbit import *
import bme280_microbit_lowmem as bme280
import utime
import radio
import værstasjon_micropython
radio.config(group=60,length=32)
radio.power = 7
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

# Oppdater regn og wind puls
RASK_INTERVAL = 75

# Hvor ofte ett radio signal skal bli sendt
RADIO_INTERVAL = 5000

# Oppdater vind måling. Må bli kjørt hvert andre sekund
SAKTE_INTERVAL = 2000

last_fast = utime.ticks_ms()
last_radio = utime.ticks_ms()
last_slow = utime.ticks_ms()

while True:
    now = utime.ticks_ms()

    # Hvis mellom nå og forrige rask interval
    if utime.ticks_diff(now, last_fast) >= RASK_INTERVAL:
        last_fast = utime.ticks_add(last_fast, RASK_INTERVAL)
        display.show(Image.BUTTERFLY)
        
        
        værstasjon_micropython.check_rain_pulse()
        værstasjon_micropython.check_wind_pulse()
    if utime.ticks_diff(now, last_radio) >= RADIO_INTERVAL:
        last_radio = utime.ticks_add(last_radio, RADIO_INTERVAL)
        display.show(Image.HAPPY)

        
        direction = værstasjon_micropython.wind_direction()
        speed = værstasjon_micropython.wind_speed()
        temp, pressure, humidity = bme.values()
        altitude = bme.altitude()
        rainfall = rain_cm()
        
        send_strings = ["W"+str(speed)+":D"+str(direction)+":R"+str(rainfall),":T"+str(temp)+":P"+str(pressure),":H"+str(humidity)+":A"+str(altitude)]
        for send_string in send_strings:
            radio.send(send_string)
            print("Sent original string")

            sleep(100)
        # Reset rainfall counter so next interval reports per-interval rainfall
        reset_rain()
    if utime.ticks_diff(now, last_slow) >= SAKTE_INTERVAL:
        last_slow = utime.ticks_add(last_slow, SAKTE_INTERVAL)
        display.show(Image.ARROW_E)
        
        værstasjon_micropython.update_wind_speed()


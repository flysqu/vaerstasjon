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
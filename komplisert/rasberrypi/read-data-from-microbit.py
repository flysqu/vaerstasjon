import serial.tools.list_ports
import sqlite3
import datetime
import mysql.connector
import re

ser: serial.Serial
initialized = False

# Port on Rasberry Pi is called "/dev/ttyACM0". 
# For testing it is set here to the windows value COM3
port: str = "COM5"

# Connect to MySQL
cnx = mysql.connector.connect(user='weather_python', password='password',
                              host='127.0.0.1',
                              database='database')

def insert_data(data):
    """Insert parsed data dict into MySQL. Expects keys:
    Wind Speed, Wind Direction, Rainfall, Pressure, Humidity, Altitude
    """
    if not data:
        print("insert_data: no data to insert")
        return

    add_weather = (
        "INSERT INTO weather_data "
        "(wind_speed, wind_direction, rainfall, pressure, humidity, altitude, temperature, time) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )

    wind_speed = data.get("Wind Speed")
    wind_dir = data.get("Wind Direction")
    rainfall = data.get("Rainfall")
    pressure = data.get("Pressure")
    humidity = data.get("Humidity")
    altitude = data.get("Altitude")
    temperature = data.get("Temperature")


    timestamp = datetime.datetime.now()

    values = (wind_speed, wind_dir, rainfall, pressure, humidity, altitude, temperature, timestamp)

    try:
        conn = mysql.connector.connect(user='weather_python', password='password',
                                       host='127.0.0.1', database='database')
        cursor = conn.cursor()
        cursor.execute(add_weather, values)
        conn.commit()
        cursor.close()
        conn.close()
        print("Inserted data at", timestamp)
    except Exception as e:
        print("Failed to insert data:", e)
        print("Data was:", data)

def short_to_long_name(key):
    switch={
        "W": "Wind Speed",
        "D": "Wind Direction",
        "R": "Rainfall",
        "T": "Temperature",
        "P": "Pressure",
        "H": "Humidity",
        "A": "Altitude"
    }
    return switch.get(key)

def process_data(data: str):
    """Parse raw serial line into a dictionary of values.
    Handles noisy input by stripping quotes/brackets and extracting the first letter as the key.
    Returns a dict with human-readable keys (see short_to_long_name) or None on parse failure."""
    if not data:
        return None

    data_processed = data.rstrip().replace(" ","")
    parts = data_processed.split(":")
    data_dict = {}

    for part in parts:
        # Clean up common noisy characters
        p = part.strip().strip("'\"[],\n\r ")
        if not p:
            continue

        # Find the first alphabetic key character
        m = re.match(r"^[^A-Za-z]*([A-Za-z])(.*)$", p)
        if not m:
            continue
        key_char = m.group(1)
        val_raw = m.group(2)

        key_name = short_to_long_name(key_char)
        if not key_name:
            # Unknown key, skip
            continue

        # Clean value: remove stray trailing characters like ',' or ']'
        val_clean = val_raw.strip().strip("'\"[],")

        # Try to parse numeric values where appropriate
        if key_char in ("W", "R", "T", "P", "H", "A"):
            # Extract first numeric substring
            num_match = re.search(r"-?\d+\.?\d*", val_clean)
            if num_match:
                try:
                    data_dict[key_name] = float(num_match.group(0))
                    continue
                except Exception:
                    pass
        # For non-numeric (e.g., direction), keep as string
        data_dict[key_name] = val_clean

    # Return the parsed dict if we have at least wind and temperature as minimal sanity check
    if data_dict and ("Wind Speed" in data_dict or "Temperature" in data_dict):
        return data_dict
    return None

def add_data_to_database(data: str):
    time = datetime.datetime.now()
    time_str = f"{time.day}/{time.month}/{time.year} - {time.hour}:{time.minute}"

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO weatherData (time, data) VALUES (?, ?)", (time_str, data))
    conn.commit()
    conn.close()

ports = serial.tools.list_ports.comports()
if len(ports) == 0:
    print("The micro:bit is not connected. Please connect it")
    quit()
for _port in ports:
    print(f"{_port.device}: {_port.description}")

# Use the first detected port by default (adjust if you want to pick a different one)
port = ports[0].device
print(f"Using port: {port}")

def init_connection():
    global initialized
    global ser
    global port

    if initialized:
        return
    else:
        initialized = True

    try:
        ser = serial.Serial(port, 9600, timeout=1)
    except:
        print("The port wasnt found.")
        print("Check if the port is set correctly and that the micro:bit is connected")
        quit()

    print("")
    print("Starting to recieve data from micro:bit")
    print("Press Ctrl+C to quit the program")

def main_loop():
    global port
    global initialized
    global ser
    
    if not initialized:
        return

    while True:
        try:
            raw = ser.readline()
            try:
                data = raw.decode('utf-8')
            except UnicodeDecodeError:
                # Replace invalid bytes so we don't crash; log raw bytes for debugging
                print("Warning: UnicodeDecodeError when decoding serial data; invalid bytes replaced")
                print("Raw bytes:", raw)
                data = raw.decode('utf-8', errors='replace')

            if not data:
                # nothing read
                continue

            data = process_data(data)
            print(data)
            if data:
                insert_data(data)
            else:
                #print("Failed to parse data:", data)
                continue

        except serial.SerialException:
            print("The micro:bit was disconnected prematurely.")
            print("The program will pause until it is reconnected")
            
            disconnected = True
            while disconnected:
                try:
                    ser = serial.Serial(port, 9600, timeout=1)
                    disconnected = False
                except serial.SerialException:
                    pass
        except KeyboardInterrupt:
            print("\nProgram terminated by user")
            ser.close()
            break

# Initialize connection and start reading from the micro:bit
init_connection()
main_loop()
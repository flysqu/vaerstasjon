import serial.tools.list_ports
from dataclasses import dataclass
from typing import Optional
import threading
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn


@dataclass
class WeatherData:
    speed: int
    direction: str
    rain: int
    temperature: float
    pressure: Optional[float] = None
    humidity: Optional[int] = None
    altitude: Optional[float] = None


def parse_weather_line(line: str) -> Optional[WeatherData]:
    line = line.strip()
    if not line:
        return None

    parts = [part for part in line.split(":") if part]
    values = {}

    for part in parts:
        key = part[0]
        value = part[1:]
        if not value:
            return None

        try:
            if key == "W":
                values["speed"] = int(value)
            elif key == "D":
                values["direction"] = str(value)
            elif key == "R":
                values["rain"] = int(value)
            elif key == "T":
                values["temperature"] = float(value)
            elif key == "P":
                values["pressure"] = float(value)
            elif key == "H":
                values["humidity"] = int(value)
            elif key == "A":
                values["altitude"] = float(value)
            else:
                return None
        except:
            return None

    required = {"speed", "direction", "rain", "temperature"}
    if not required.issubset(values.keys()):
        return None

    return WeatherData(
        speed=values["speed"],
        direction=values["direction"],
        rain=values["rain"],
        temperature=values["temperature"],
        pressure=values.get("pressure"),
        humidity=values.get("humidity"),
    )


latest_weather: Optional[WeatherData] = None


def read_serial_data():
    global latest_weather
    ser = serial.Serial('COM4', 9600, timeout=1)
    while True:
        raw = ser.readline()
        if not raw:
            continue

        try:
            line = raw.decode('utf-8', errors='replace').strip()
        except Exception:
            continue

        if not line:
            continue

        weather = parse_weather_line(line)
        if weather is None:
            print(f"Invalid line: {line}")
            continue

        latest_weather = weather
        print(line)
        print(weather)


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    html = """
    <html>
    <head>
        <title>Weather Station</title>
    </head>
    <body>
        <h1>Weather Data</h1>
        <div id="weather-data">
            <p>Loading...</p>
        </div>
        <script>
            async function updateWeather() {
                try {
                    const response = await fetch('/api/data');
                    const data = await response.json();
                    if (data) {
                        document.getElementById('weather-data').innerHTML = `
                            <p>Speed: ${data.speed}</p>
                            <p>Direction: ${data.direction}</p>
                            <p>Rain: ${data.rain}</p>
                            <p>Temperature: ${data.temperature}°C</p>
                            ${data.pressure ? `<p>Pressure: ${data.pressure} hPa</p>` : ''}
                            ${data.humidity ? `<p>Humidity: ${data.humidity}%</p>` : ''}
                            ${data.altitude ? `<p>Altitude: ${data.altitude} m</p>` : ''}
                        `;
                    } else {
                        document.getElementById('weather-data').innerHTML = '<p>No data available</p>';
                    }
                } catch (error) {
                    document.getElementById('weather-data').innerHTML = '<p>Error loading data</p>';
                }
            }
            updateWeather();
            setInterval(updateWeather, 5000);  // Update every 5 seconds
        </script>
    </body>
    </html>
    """
    return html


@app.get("/api/data")
async def get_weather_data():
    return latest_weather


if __name__ == "__main__":
    # Start the serial reading thread
    thread = threading.Thread(target=read_serial_data, daemon=True)
    thread.start()

    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
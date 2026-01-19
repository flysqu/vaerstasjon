<?php
// show errors (development only)
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// no direct DB connection from this page; we use the API endpoint for data
// The top-level PHP is kept for server-side convenience (e.g., default date)
$default_date = date('Y-m-d');
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vardø VGS Værstasjon</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }

        .controls {
            margin-bottom: 12px;
        }

        .latest {
            margin-top: 12px;
            display: flex;
            gap: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .latest div {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }

        #status {
            margin-top: 10px;
            color: #b00
        }

        /* Fixed-height container prevents the chart growing on each update */
        .chart-container {
            height: 400px;
            max-height: 600px;
        }

        canvas#chart {
            width: 100% !important;
            height: 100% !important;
            display: block;
        }
    </style>
</head>

<body>
    <h1>Vardø VGS — Værstasjon</h1>

    <div class="controls">
        <label for="date">Date:</label>
        <input type="date" id="date" value="<?php echo $default_date ?>">
        <button id="loadBtn">Load</button>
        <span id="status"></span>
    </div>

    <div class="chart-container"><canvas id="chart"></canvas></div>
    
    <p style="text-align: center; margin-top: 20px; margin-bottom: 2px;">Latest Data</p>
    <div class="latest" id="latest">
        <div id="latest-temp">Temperature: —</div>
        <div id="latest-wind">Wind speed: —</div>
        <div id="latest-pressure">Pressure: —</div>
        <div id="latest-humidity">Humidity: —</div>
        <div id="latest-rain">Rainfall: —</div>
        <div id="latest-alt">Altitude: —</div>
        <div id="latest-dir">Wind dir: —</div>
    </div>

    <script>
        const ctx = document.getElementById('chart').getContext('2d');
        let chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgb(255, 99, 132)',
                        pointBackgroundColor: 'rgb(255, 99, 132)',
                        pointBorderColor: 'rgb(255, 99, 132)',
                        yAxisID: 'y',
                        tension: 0.2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        spanGaps: true,
                        showLine: true,
                        fill: false
                    },
                    {
                        label: 'Wind speed (mph)',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgb(54, 162, 235)',
                        pointBackgroundColor: 'rgb(54, 162, 235)',
                        pointBorderColor: 'rgb(54, 162, 235)',
                        yAxisID: 'y1',
                        tension: 0.2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        spanGaps: true,
                        showLine: true,
                        fill: false
                    }
                ]
            },
            options: {
                scales: {
                    // Use a category x-axis (labels are time strings) to avoid adapter dependency
                    x: { type: 'category', title: { display: true, text: 'Time' } },
                    y: { type: 'linear', position: 'left', title: { display: true, text: '°C' } },
                    y1: { type: 'linear', position: 'right', title: { display: true, text: 'mph' }, grid: { drawOnChartArea: false } }
                },
                plugins: { legend: { display: true } },
                maintainAspectRatio: false
            }
        });

        document.getElementById('loadBtn').addEventListener('click', loadData);

        function fmt(n) { return (n === null || n === undefined) ? '—' : n; }

        async function loadData() {
            const date = document.getElementById('date').value;
            const statusEl = document.getElementById('status');
            statusEl.textContent = 'Loading...';
            try {
                const res = await fetch('api/data.php?date=' + encodeURIComponent(date));
                statusEl.textContent = 'HTTP ' + res.status;
                const text = await res.text();
                let json;
                try {
                    json = JSON.parse(text);
                } catch (err) {
                    statusEl.textContent = 'Invalid JSON response';
                    console.error('Invalid JSON from API:', text);
                    return;
                }

                if (json.error) {
                    statusEl.textContent = 'API error: ' + json.error;
                    console.error('API error:', json);
                    return;
                }

                const series = json.series || [];
                if (!series.length) {
                    statusEl.textContent = 'No data for ' + date;
                    chart.data.labels = [];
                    chart.data.datasets[0].data = [];
                    chart.data.datasets[1].data = [];
                    chart.update();
                    // ensure the chart recalculates layout to fit the fixed container
                    chart.resize();
                } else {
                    console.log('series (first 10):', series.slice(0, 10));
                    statusEl.textContent = 'Loaded ' + series.length + ' points';
                    // Use time strings as category labels and numeric arrays for datasets
                    const labels = series.map(s => s.time || '');
                    chart.data.labels = labels;

                    const temperature = series.map(s => (s.temperature === null || s.temperature === undefined) ? null : Number(s.temperature));
                    chart.data.datasets[0].data = temperature;

                    const wind_speed = series.map(s => (s.wind_speed === null || s.wind_speed === undefined) ? null : Number(s.wind_speed));
                    chart.data.datasets[1].data = wind_speed;

                    const numTemp = temperature.filter(v => typeof v === 'number' && !isNaN(v)).length;
                    const numWind = wind_speed.filter(v => typeof v === 'number' && !isNaN(v)).length;
                    if (!numTemp && !numWind) {
                        statusEl.textContent = 'No numeric data to plot for ' + date;
                        console.warn('No numeric temperature or wind data:', { temperature, wind_speed });
                    }

                    chart.update();
                    // enforce layout update
                    chart.resize();
                }

                const latest = json.latest || {};
                console.log(latest)
                document.getElementById('latest-temp').textContent = 'Temperature: ' + fmt(latest.temperature);
                document.getElementById('latest-wind').textContent = 'Wind speed: ' + fmt(latest.wind_speed);
                document.getElementById('latest-pressure').textContent = 'Pressure: ' + fmt(latest.pressure);
                document.getElementById('latest-humidity').textContent = 'Humidity: ' + fmt(latest.humidity);
                document.getElementById('latest-rain').textContent = 'Rainfall: ' + fmt(latest.rainfall);
                document.getElementById('latest-alt').textContent = 'Altitude: ' + fmt(latest.altitude);
                document.getElementById('latest-dir').textContent = 'Wind direction: ' + (latest.wind_direction || '—');

            } catch (e) {
                document.getElementById('status').textContent = 'Fetch failed: ' + e;
                console.error(e);
            }
        }

        // Load today's data on first render
        loadData();
    </script>
</body>
</html>
# Speedtest Dashboard

This project is a Panel-based dashboard for running and visualizing internet speed tests. It uses the `speedtest` library to measure download, upload, and ping speeds, and stores the results in a SQLite database. The dashboard displays the results in real-time using HoloViews and Panel.

## Features

- Run internet speed tests manually or automatically at specified intervals.
- Store speed test results in a SQLite database.
- Display results in a table and plot download/upload speeds over time.
- Show the most recent speed test results.

## Requirements

- Python 3.7+
- Panel
- HoloViews
- Pandas
- Param
- Requests
- Speedtest-cli
- SQLAlchemy
- Dateutil

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/pgierz/speedtest-docker.git
    cd speedtest-docker
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the application:
    ```sh
    python app.py
    ```

2. Open your web browser and navigate to `http://localhost:5006` to view the dashboard.

3. Alternatively, you can run the application using Docker:
    ```sh
    docker build -t speedtest-dashboard .
    docker run -d --name speedtest-dashboard \
           --restart unless-stopped \
           -p 5006:5006 \
           -v /var/lib/speedtest-dashboard:/data \
           speedtest-dashboard
    ```

## Configuration

- You can configure the update interval for automatic speed tests by adjusting the `update_interval` parameter in the dashboard.

## License

This project is licensed under the MIT License.

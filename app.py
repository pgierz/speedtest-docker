import asyncio
from datetime import datetime

import holoviews as hv
import pandas as pd
import panel as pn
import param
import requests
import speedtest
from dateutil import parser
from sqlalchemy import Column, DateTime, Float, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

pn.extension("tabulator", sizing_mode="stretch_width")
hv.extension("bokeh")

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:////data/speedtest.db")
Session = sessionmaker(bind=engine)


class SpeedTest(Base):
    __tablename__ = "speedtests"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    download = Column(Float)
    upload = Column(Float)
    ping = Column(Float)


Base.metadata.create_all(engine)


class SpeedtestDashboard(param.Parameterized):
    update_interval = param.Integer(default=60, bounds=(10, 3600))
    run_test = param.Action(lambda self: self._run_speedtest())

    def __init__(self, **params):
        super().__init__(**params)
        self.load_data_from_db()

    def load_data_from_db(self):
        session = Session()
        results = (
            session.query(SpeedTest)
            .order_by(SpeedTest.timestamp.desc())
            .limit(100)
            .all()
        )
        self.data = pd.DataFrame(
            [(r.timestamp, r.download, r.upload, r.ping) for r in results],
            columns=["timestamp", "download", "upload", "ping"],
        )
        self.stream = hv.streams.Buffer(self.data, index=False, length=100)
        session.close()

    def _run_speedtest(self):
        try:
            s = speedtest.Speedtest()
            s.get_best_server()
            s.download()
            s.upload()
            results = s.results.dict()

            timestamp = parser.isoparse(results["timestamp"])
            download = results["download"] / 1_000_000  # Convert to Mbps
            upload = results["upload"] / 1_000_000  # Convert to Mbps
            ping = results["ping"]

            # Save to database
            session = Session()
            new_test = SpeedTest(
                timestamp=timestamp, download=download, upload=upload, ping=ping
            )
            session.add(new_test)
            session.commit()
            session.close()

            new_data = pd.DataFrame(
                {
                    "timestamp": [timestamp],
                    "download": [download],
                    "upload": [upload],
                    "ping": [ping],
                }
            )

            self.stream.send(new_data)
        except (speedtest.SpeedtestException, requests.RequestException) as e:
            print(f"Error running speedtest: {e}")
            # Optionally, update the UI to show the error
            error_data = pd.DataFrame(
                {
                    "timestamp": [datetime.now()],
                    "download": [0],
                    "upload": [0],
                    "ping": [0],
                }
            )
            self.stream.send(error_data)

    @param.depends("stream.data", watch=True)
    def get_table(self):
        return pn.widgets.Tabulator(self.stream.data, height=200)

    @param.depends("stream.data", watch=True)
    def get_plot(self):
        plot = hv.Curve(
            self.stream.data, "timestamp", "download", label="Download (Mbps)"
        ) * hv.Curve(self.stream.data, "timestamp", "upload", label="Upload (Mbps)")
        return plot.opts(
            width=800, height=400, legend_position="top_left", title="Speed Over Time"
        )

    @param.depends("stream.data", watch=True)
    def get_current_speed(self):
        if not self.stream.data.empty:
            last_row = self.stream.data.iloc[-1]
            return pn.pane.Markdown(
                f"""
            ## Current Speed
            - Timestamp: {last_row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
            - Download: {last_row['download']:.2f} Mbps
            - Upload: {last_row['upload']:.2f} Mbps
            - Ping: {last_row['ping']:.2f} ms
            """
            )
        return pn.pane.Markdown("No data available yet.")

    def view(self):
        return pn.Column(
            pn.Row(
                pn.Param(self.param.update_interval, width=200),
                self.param.run_test,
            ),
            pn.Row(self.get_current_speed, self.get_plot),
            self.get_table,
        )


dashboard = SpeedtestDashboard()


async def update():
    while True:
        dashboard._run_speedtest()
        await asyncio.sleep(dashboard.update_interval)


pn.state.add_periodic_callback(update, period=1000)

app = pn.serve(dashboard.view, port=5006, show=True)

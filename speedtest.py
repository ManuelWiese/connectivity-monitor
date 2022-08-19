import json
import logging
import subprocess
import time


from prometheus_client import Counter, Gauge


class Speedtest:
    def __init__(self, host, timeout=120):
        self.host = host
        self.timeout = timeout
        self.create_prometheus_metrics()

    def create_prometheus_metrics(self):
        host = self.host.replace('.', '_')
        host = host.replace(':', '_')
        host = host.replace('-', '_')

        self.speedtest_failed_counter = Counter(
            f"connectivity_monitor_speedtest_{host}_failed_total",
            f"Total of times the speedtest failed for host {self.host}"
        )

        self.json_failed_counter = Counter(
            f"connectivity_monitor_speedtest_{host}_json_failed_total",
            f"Total of times of json parse errors when speedtesting host {self.host}"
        )

        self.ping_gauge = Gauge(
            f"connectivity_monitor_speedtest_{host}_ping_seconds",
            "Ping of host {self.host}"
        )

        self.jitter_gauge = Gauge(
            f"connectivity_monitor_speedtest_{host}_jitter_seconds",
            "Ping-Jitter of host {self.host}"
        )

        self.download_gauge = Gauge(
            f"connectivity_monitor_speedtest_{host}_download_bits_per_second",
            "Download speed of host {self.host}"
        )

        self.upload_gauge = Gauge(
            f"connectivity_monitor_speedtest_{host}_upload_bits_per_second",
            "Upload speed of host {self.host}"
        )

    def __str__(self):
        return f"Speedtest({self.host})"
        
    def __call__(self):
        popen = subprocess.Popen(
            ["timeout", str(self.timeout), "SpeedTest", "--test-server", self.host, "--output", "json"],
            shell=False,
            stdout=subprocess.PIPE
        )

        while popen.poll() is None:
            time.sleep(1)

        exit_code = popen.poll()

        if exit_code:
            self.speedtest_failed_counter.inc()

            self.ping_gauge.set(float("nan"))
            self.jitter_gauge.set(float("nan"))
            self.download_gauge.set(0.)
            self.upload_gauge.set(0.)

            return

        try:
            output = popen.stdout.read().decode()
            data = json.loads(output)
            logging.debug(f"SpeedTest data: {data}")
            self.ping_gauge.set(int(data['ping']) / 1000.)
            self.jitter_gauge.set(int(data['jitter']) / 1000.)
            self.download_gauge.set(float(data['download']))
            self.upload_gauge.set(float(data['upload']))

        except Exception as e:
            logging.exception(e)
            self.json_failed_counter.inc()


if __name__ == "__main__":
    import threading
    from schedule_background import schedule_background

    kill_event = threading.Event()

    thread = schedule_background(
        Speedtest("d-speed.bi-host.net:8080"),
        interval=60,
        kill_event=kill_event
    )

    try:
        thread.join()
    except KeyboardInterrupt:
        kill_event.set()
        thread.join()

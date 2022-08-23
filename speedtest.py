import json
import logging
import subprocess
import time


from prometheus_client import Counter, Gauge


class Speedtest:
    def __init__(self, host, metrics, timeout=120):
        self.host = host
        self.metrics = metrics
        self.timeout = timeout

        self._host = self.host.replace('.', '_')
        self._host = self._host.replace(':', '_')
        self._host = self._host.replace('-', '_')

        self.metrics.add_host(self._host)

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
            self.metrics.speedtest_failed_counter.labels(self._host).inc()

            self.metrics.ping_gauge.labels(self._host).set(float("nan"))
            self.metrics.jitter_gauge.labels(self._host).set(float("nan"))
            self.metrics.download_gauge.labels(self._host).set(0.)
            self.metrics.upload_gauge.labels(self._host).set(0.)

            return

        try:
            output = popen.stdout.read().decode()
            data = json.loads(output)
            logging.debug(f"SpeedTest data: {data}")
            self.metrics.ping_gauge.labels(self._host).set(int(data['ping']) / 1000.)
            self.metrics.jitter_gauge.labels(self._host).set(int(data['jitter']) / 1000.)
            self.metrics.download_gauge.labels(self._host).set(float(data['download']))
            self.metrics.upload_gauge.labels(self._host).set(float(data['upload']))

        except Exception as e:
            logging.exception(e)
            self.metrics.json_failed_counter.labels(self._host).inc()


class SpeedtestMetrics:
    def __init__(self):
        self.speedtest_failed_counter = Counter(
            f"connectivity_monitor_speedtest_failed_total",
            f"Total of times the speedtest failed for host",
            ["host"]
        )

        self.json_failed_counter = Counter(
            f"connectivity_monitor_speedtest_json_failed_total",
            f"Total of times of json parse errors when speedtesting host",
            ["host"]
        )

        self.ping_gauge = Gauge(
            f"connectivity_monitor_speedtest_ping_seconds",
            "Ping of host",
            ["host"]
        )

        self.jitter_gauge = Gauge(
            f"connectivity_monitor_speedtest_jitter_seconds",
            "Ping-Jitter of host",
            ["host"]
        )

        self.download_gauge = Gauge(
            f"connectivity_monitor_speedtest_download_bits_per_second",
            "Download speed of host",
            ["host"]
        )

        self.upload_gauge = Gauge(
            f"connectivity_monitor_speedtest_upload_bits_per_second",
            "Upload speed of host",
            ["host"]
        )

    def add_host(self, host):
        self.speedtest_failed_counter.labels(host)
        self.json_failed_counter.labels(host)
        self.ping_gauge.labels(host)
        self.jitter_gauge.labels(host)
        self.download_gauge.labels(host)
        self.upload_gauge.labels(host)


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

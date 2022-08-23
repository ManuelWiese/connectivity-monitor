import logging
import subprocess
import time

import parse

from prometheus_client import Counter, Gauge


class Ping:
    def __init__(self, host, metrics, count=5):
        self.host = host
        self.metrics = metrics
        self.count = count

        self.parse_packet_statistics = parse.compile(
            "{transmitted:d} packets transmitted, {received:d} received, {loss:g}% packet loss, time {time:d}ms"
        )

        self.parse_time_statistics = parse.compile(
            "rtt min/avg/max/mdev = {rtt_min:f}/{rtt_avg:f}/{rtt_max:f}/{rtt_mdev:f} ms"
        )

        self._host = self.host.replace('.', '_')
        self.metrics.add_host(self._host)

    def __str__(self):
        return f"Ping({self.host}, count={self.count})"

    def __call__(self):
        popen = subprocess.Popen(
            ["ping", "-c", str(self.count), self.host],
            shell=False,
            stdout=subprocess.PIPE
        )

        while popen.poll() is None:
            time.sleep(1)

        exit_code = popen.poll()

        if exit_code:
            self.metrics.not_reachable_counter.labels(self._host).inc()
            self.metrics.transmitted_gauge.labels(self._host).set(0.)
            self.metrics.received_gauge.labels(self._host).set(0.)
            self.metrics.loss_gauge.labels(self._host).set(1.)
            self.metrics.time_gauge.labels(self._host).set(float("nan"))

            self.metrics.rtt_gauge.labels(self._host, "min").set(float("nan"))
            self.metrics.rtt_gauge.labels(self._host, "avg").set(float("nan"))
            self.metrics.rtt_gauge.labels(self._host, "max").set(float("nan"))
            self.metrics.rtt_gauge.labels(self._host, "mdev").set(float("nan"))

            return

        try:
            output = popen.stdout.read().decode()

            packet_statistics = self.parse_packet_statistics.search(output)
            logging.debug(f"packet_statistics of {self.host}: {packet_statistics.named}")

            self.metrics.transmitted_gauge.labels(self._host).set(packet_statistics['transmitted'])
            self.metrics.received_gauge.labels(self._host).set(packet_statistics['received'])
            self.metrics.loss_gauge.labels(self._host).set(packet_statistics['loss'] / 100.)
            self.metrics.time_gauge.labels(self._host).set(packet_statistics['time'] / 1000.)

            time_statistics = self.parse_time_statistics.search(output)
            logging.debug(f"time_statistics of {self.host}: {time_statistics.named}")

            self.metrics.rtt_gauge.labels(self._host, "min").set(time_statistics['rtt_min'] / 1000.)
            self.metrics.rtt_gauge.labels(self._host, "avg").set(time_statistics['rtt_avg'] / 1000.)
            self.metrics.rtt_gauge.labels(self._host, "max").set(time_statistics['rtt_max'] / 1000.)
            self.metrics.rtt_gauge.labels(self._host, "mdev").set(time_statistics['rtt_mdev'] / 1000.)
        except Exception as e:
            logging.exception(e)
            self.metrics.parse_failed_counter.labels(self._host).inc()


class PingMetrics:
    def __init__(self):
        self.not_reachable_counter = Counter(
            f"connectivity_monitor_ping_not_reachable_total",
            f"Total of times the host was not reachable",
            ['host']
        )

        self.parse_failed_counter = Counter(
            f"connectivity_monitor_ping_parse_failed_total",
            f"Total of times of parse errors when pinging host",
            ['host']
        )

        self.transmitted_gauge = Gauge(
            f"connectivity_monitor_ping_packets_transmitted",
            "Packets transmitted to host",
            ['host']
        )

        self.received_gauge = Gauge(
            f"connectivity_monitor_ping_packets_received",
            "Packets received from host",
            ['host']
        )

        self.loss_gauge = Gauge(
            f"connectivity_monitor_ping_packet_loss_ratio",
            "Packet loss ratio of host",
            ['host']
        )

        self.time_gauge = Gauge(
            f"connectivity_monitor_ping_time_seconds",
            "Runtime of ping command of host",
            ['host']
        )

        self.rtt_gauge = Gauge(
            f"connectivity_monitor_ping_rtt_seconds",
            "Roundtrip-time of host in seconds",
            ['host', 'statistic']
        )

    def add_host(self, host):
        self.not_reachable_counter.labels(host)
        self.parse_failed_counter.labels(host)
        self.transmitted_gauge.labels(host)
        self.received_gauge.labels(host)
        self.loss_gauge.labels(host)
        self.time_gauge.labels(host)

        self.rtt_gauge.labels(host, 'min')
        self.rtt_gauge.labels(host, 'avg')
        self.rtt_gauge.labels(host, 'max')
        self.rtt_gauge.labels(host, 'mdev')


if __name__ == "__main__":
    import logging
    import threading
    from schedule_background import schedule_background

    logging.basicConfig(level="DEBUG")

    kill_event = threading.Event()

    thread = schedule_background(
        Ping("www.google.de", count=5),
        interval=10,
        kill_event=kill_event
    )

    try:
        thread.join()
    except KeyboardInterrupt:
        kill_event.set()
        thread.join()

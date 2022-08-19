import logging
import subprocess
import time

import parse

from prometheus_client import Counter, Gauge


class Ping:
    def __init__(self, host, count=5):
        self.host = host
        self.count = count

        self.parse_packet_statistics = parse.compile(
            "{transmitted:d} packets transmitted, {received:d} received, {loss:g}% packet loss, time {time:d}ms"
        )

        self.parse_time_statistics = parse.compile(
            "rtt min/avg/max/mdev = {rtt_min:f}/{rtt_avg:f}/{rtt_max:f}/{rtt_mdev:f} ms"
        )

        self.create_prometheus_metrics()

    def create_prometheus_metrics(self):
        host = self.host.replace('.', '_')

        self.not_reachable_counter = Counter(
            f"connectivity_monitor_ping_{host}_not_reachable_total",
            f"Total of times the host {self.host} was not reachable"
        )

        self.parse_failed_counter = Counter(
            f"connectivity_monitor_ping_{host}_parse_failed_total",
            f"Total of times of parse errors when pinging host {self.host}"
        )

        self.transmitted_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_packets_transmitted",
            "Packets transmitted to host {self.host}"
        )

        self.received_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_packets_received",
            "Packets received from host {self.host}"
        )

        self.loss_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_packet_loss_ratio",
            "Packet loss ratio of host {self.host}"
        )

        self.time_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_time_seconds",
            "Runtime of ping command of host {self.host}"
        )

        self.rtt_min_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_rtt_min_seconds",
            "Min roundtrip-time of host {self.host} in seconds"
        )

        self.rtt_avg_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_rtt_avg_seconds",
            "Average roundtrip-time of host {self.host} in seconds"
        )

        self.rtt_max_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_rtt_max_seconds",
            "Max roundtrip-time of host {self.host} in seconds"
        )

        self.rtt_mdev_gauge = Gauge(
            f"connectivity_monitor_ping_{host}_rtt_mdev_seconds",
            "Standard deviation of roundtrip-time of host {self.host} in seconds"
        )

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
            self.not_reachable_counter.inc()
            self.transmitted_gauge.set(0.)
            self.received_gauge.set(0.)
            self.loss_gauge.set(1.)
            self.time_gauge.set(float("nan"))

            self.rtt_min_gauge.set(float("nan"))
            self.rtt_avg_gauge.set(float("nan"))
            self.rtt_max_gauge.set(float("nan"))
            self.rtt_mdev_gauge.set(float("nan"))

            return

        try:
            output = popen.stdout.read().decode()

            packet_statistics = self.parse_packet_statistics.search(output)
            logging.debug(f"packet_statistics of {self.host}: {packet_statistics.named}")

            self.transmitted_gauge.set(packet_statistics['transmitted'])
            self.received_gauge.set(packet_statistics['received'])
            self.loss_gauge.set(packet_statistics['loss'] / 100.)
            self.time_gauge.set(packet_statistics['time'] / 1000.)

            time_statistics = self.parse_time_statistics.search(output)
            logging.debug(f"time_statistics of {self.host}: {time_statistics.named}")

            self.rtt_min_gauge.set(time_statistics['rtt_min'] / 1000.)
            self.rtt_avg_gauge.set(time_statistics['rtt_avg'] / 1000.)
            self.rtt_max_gauge.set(time_statistics['rtt_max'] / 1000.)
            self.rtt_mdev_gauge.set(time_statistics['rtt_mdev'] / 1000.)
        except Exception as e:
            logging.exception(e)
            self.parse_failed_counter.inc()


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

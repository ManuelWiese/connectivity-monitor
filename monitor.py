import logging
import random
import sched
import time

from ping3 import ping
from prometheus_client import start_http_server, Counter, Gauge, Summary
import yaml


def main():
    config = load_config()
    configure_logger(config['logging'])

    start_http_server(config['prometheus']['port'])

    scheduler = sched.scheduler(time.time, time.sleep)

    ping_schedules = [PingSchedule(server, config['ping']['interval'], scheduler) for server in config['ping']['hosts']]

    scheduler.run()


def load_config():
    with open("config.yaml", "r") as stream:
        config = yaml.safe_load(stream)

    return config


def configure_logger(logging_config):
    filename = logging_config['filename'] if 'filename' in logging_config else None
    level = logging_config['level'].upper() if 'level' in logging_config else "DEBUG"
    format = logging_config['format'] if 'format' in logging_config else None
    logging.basicConfig(
        filename=filename,
        level=level,
        format=format
    )


class PingSchedule:
    def __init__(self, server: str, interval: int, scheduler: sched.scheduler, priority: int = 1):
        self.server = server
        self.interval = interval
        self.scheduler = scheduler
        self.priority = priority

        self.not_reachable_counter = Counter(
            f"connectivity_monitor_{self.server.replace('.', '_')}_not_reachable_total",
            f"Total of times the host {self.server} was not reachable"
        )

        self.ping_gauge = Gauge(
            f"connectivity_monitor_{self.server.replace('.', '_')}_ping_seconds",
            "Ping time of host {self.server} in seconds"
        )

        start_delay = random.random() * self.interval
        logging.info(f"Scheduling ping {self.server} in {start_delay}s")
        self.schedule(start_delay)

    def schedule(self, _time):
        self.scheduler.enter(
            _time,
            self.priority,
            type(self).run,
            argument=(self, )
        )

    def run(self):
        self.schedule(self.interval)
        logging.info(f"Pinging {self.server}")
        result = ping(self.server)

        if result is None:
            self.not_reachable_counter.inc()

        self.ping_gauge.set(result)
        logging.info(f"Ping of {self.server}: {result}")


if __name__ == "__main__":
    main()

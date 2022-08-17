import argparse
import logging
import random
import threading
import time

from prometheus_client import start_http_server
import yaml

from ping import Ping
from schedule_background import schedule_background


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prometheus_port", type=int, default=8000)
    arguments = parser.parse_args()

    config = load_config()
    configure_logger(config['logging'])

    start_http_server(arguments.prometheus_port)

    kill_event = threading.Event()

    threads = []

    for host in config['ping']['hosts']:
        delay = random.random() * config['ping']['random_delay'] if config['ping']['random_delay'] else 0
        thread = schedule_background(
            Ping(host),
            delay=delay,
            interval=config['ping']['interval'],
            kill_event=kill_event
        )
        threads.append(thread)

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        kill_event.set()
        for thread in threads:
            thread.join()


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


if __name__ == "__main__":
    main()

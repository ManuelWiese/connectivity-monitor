# connectivity-monitor

A docker container to monitor network ping times internet speed.
Subprocesses are scheduled in background threads, results are published
to a prometheus endpoint.

## How to use connectivity-monitor

The container can be pulled from dockerhub and started using:
```console
docker run --rm -p 8000:8000 -v /path/to/config.yaml:/etc/connectivity_monitor/config.yaml manuelwiese/connectivity_monitor
```
In this example the container will report metrics on port 8000.

## Example configuration

To configure new targets for ping and speedtest, you can modify the provided config.yaml file.
To find new speedtest servers, use the speedtest-cli python package or [SpeedTest++](https://github.com/taganaka/SpeedTest).

```yaml
logging:
  # when logging to a file use a docker volume or bind to persist the file
  filename: null
  level: info
  format: '%(asctime)s | %(levelname)s | %(message)s'

ping:
  # initial random delay in seconds, 10->first start will be between 0 and 10 seconds
  random_delay: 10
  # run ping every 30 seconds
  interval: 30
  # list of hosts to ping
  hosts:
    - www.google.de

speedtest:
  random_delay: 30
  interval: 120
  hosts:
    - d-speed.bi-host.net:8080
```
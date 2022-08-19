# connectivity-monitor

A docker container to monitor network ping times internet speed.
Subprocesses are scheduled in background threads, results are published
to a prometheus endpoint. This project uses [SpeedTest++](https://github.com/taganaka/SpeedTest) for testing download and upload speeds, since it was more reliable than speedtest-cli during my tests.

## How to use connectivity-monitor

The container can be pulled from dockerhub and started using:
```shell
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
    - 8.8.8.8

speedtest:
  random_delay: 30
  # i do not recommend using a speedtest this often, since it uses alot of bandwidth
  interval: 120
  hosts:
    - d-speed.bi-host.net:8080
```

# Building the container

To build the container on your host use

```shell
docker build -t connectivity-monitor .
```

To build the container for multiple architectures(e.g. and64 and arm64) use *docker buildx*.
The following example uses QEMU emulation support, using native nodes might be easier.

```shell
# create a new builder instance using the BuildKit docker-container
docker buildx create --name multiarch --driver docker-container --use

# inspect the current builder, boot builder if needed
docker buildx inspect --bootstrap

# this is needed when not using docker desktop for some architectures
# some architectures work without (e.g. arm64/v8 works for me on amd64)
docker run --privileged --rm tonistiigi/binfmt --install all

# use buildx to build multiarch container
# if you do not want to push directly to a registry
# you must solve the issue to export the containers from the build-containers
docker buildx build --push --platform linux/arm/v7,linux/arm64/v8,linux/amd64 --tag manuelwiese/connectivity-monitor:latest .
```
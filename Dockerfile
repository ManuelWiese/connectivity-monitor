FROM python:3.9-slim

RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

WORKDIR /etc/connectivity_monitor
COPY requirements.txt /etc/connectivity_monitor/
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY *.py /etc/connectivity_monitor/
COPY config.yaml /etc/connectivity_monitor/

EXPOSE 8000

ENTRYPOINT ["python3"]
CMD ["monitor.py"]
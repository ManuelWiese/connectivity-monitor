FROM python:3.9-slim

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    	    build-essential \
	    libcurl4-openssl-dev \
	    libxml2-dev \
	    libssl-dev \
	    cmake \
	    git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/taganaka/SpeedTest
WORKDIR /opt/SpeedTest
RUN cmake -DCMAKE_BUILD_TYPE=Release .
RUN make install


FROM python:3.9-slim
COPY --from=0 /usr/local/bin/SpeedTest /usr/local/bin/SpeedTest

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    	    libcurl4-openssl-dev \
    	    libxml2-dev \
    	    libssl-dev && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install --no-install-recommends -y iputils-ping && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /etc/connectivity_monitor
COPY requirements.txt /etc/connectivity_monitor/
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY *.py /etc/connectivity_monitor/
COPY config.yaml /etc/connectivity_monitor/

EXPOSE 8000

ENTRYPOINT ["python3", "monitor.py"]

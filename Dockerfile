FROM ghcr.io/tracetechnical/simple-restreamer:latest

RUN sysctl net.core.rmem_max
RUN echo net.core.rmem_max = 100000000 >> /etc/sysctl.conf

WORKDIR /opt/app

COPY . .

CMD [ "python3", "main.py"]

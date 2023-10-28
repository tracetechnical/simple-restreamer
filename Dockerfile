FROM ghcr.io/tracetechnical/simple-restreamer-image:latest

RUN echo net.core.rmem_max = 1000000000 >> /etc/sysctl.conf
RUN echo net.core.wmem_max = 1000000000 >> /etc/sysctl.conf
RUN sysctl -p

WORKDIR /opt/app

COPY . .

CMD [ "python3", "main.py"]

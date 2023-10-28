FROM ghcr.io/tracetechnical/simple-restreamer:latest

WORKDIR /opt/app

COPY . .

CMD [ "python3", "main.py"]

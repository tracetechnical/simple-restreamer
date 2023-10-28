FROM ghcr.io/tracetechnical/simple-restreamer-image:latest

WORKDIR /opt/app

COPY . .

CMD [ "python3", "main.py"]

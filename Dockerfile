FROM fizmath/gpu-opencv:latest

WORKDIR /opt/app

COPY . .

CMD [ "python3", "-u", "main.py"]

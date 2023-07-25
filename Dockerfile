FROM jjanzic/docker-python3-opencv

WORKDIR /opt/app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 libgl1 -y

COPY . .

CMD [ "python3", "main.py"]

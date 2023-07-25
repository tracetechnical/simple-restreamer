FROM jjanzic/docker-python3-opencv

WORKDIR /opt/app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "main.py"]
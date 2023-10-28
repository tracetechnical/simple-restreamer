FROM czentye/opencv-video-minimal:latest

# OpenCV custom build instructions from:
# https://medium.com/@galaktyk01/how-to-build-opencv-with-gstreamer-b11668fa09c
# https://github.com/junjuew/Docker-OpenCV-GStreamer/blob/master/opencv3-gstreamer1.0-Dockerfile

WORKDIR /opt/app

COPY . .

CMD [ "python3", "main.py"]

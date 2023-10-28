FROM czentye/opencv-video-minimal:latest

# OpenCV custom build instructions from:
# https://medium.com/@galaktyk01/how-to-build-opencv-with-gstreamer-b11668fa09c
# https://github.com/junjuew/Docker-OpenCV-GStreamer/blob/master/opencv3-gstreamer1.0-Dockerfile

RUN apt-get update
RUN apt-get -y install build-essential
RUN apt-get -y install pkg-config
RUN apt-get install -y libgstreamer1.0-0 \
            gstreamer1.0-plugins-base \
            gstreamer1.0-plugins-good \
            gstreamer1.0-plugins-bad \
            gstreamer1.0-plugins-ugly \
            gstreamer1.0-libav \
            gstreamer1.0-tools \
            libgstreamer1.0-dev \
            libgstreamer-plugins-base1.0-dev \
            cmake \
            protobuf-compiler \
            libgtk2.0-dev \
            ocl-icd-opencl-devg

WORKDIR /opt/app

COPY . .

CMD [ "python3", "main.py"]

FROM python:3.9.18-bullseye

# OpenCV custom build instructions from:
# https://medium.com/@galaktyk01/how-to-build-opencv-with-gstreamer-b11668fa09c
# https://github.com/junjuew/Docker-OpenCV-GStreamer/blob/master/opencv3-gstreamer1.0-Dockerfile

# Install base dependencies + gstreamer
RUN pip uninstall -y opencv-python
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
            ocl-icd-opencl-dev

# Clone OpenCV repo
WORKDIR /
RUN git clone --recursive https://github.com/skvark/opencv-python.git
WORKDIR /opencv-python
RUN export CMAKE_ARGS="-DWITH_GSTREAMER=ON -DWITH_CUDA=OFF"
RUN pip install --upgrade pip wheel
# this is the build step - the repo estimates it can take from 5
#   mins to > 2 hrs depending on your computer hardware
RUN pip wheel . --verbose
RUN pip install opencv_python*.whl

WORKDIR /opt/app

COPY . .

CMD [ "python3", "main.py"]

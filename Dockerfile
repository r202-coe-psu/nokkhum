FROM debian:sid
RUN echo 'deb http://mirror.psu.ac.th/debian/ sid main contrib non-free' > /etc/apt/sources.list
RUN echo 'deb http://mirror.kku.ac.th/debian/ sid main contrib non-free' >> /etc/apt/sources.list
RUN echo 'deb http://www.deb-multimedia.org sid main non-free' >> /etc/apt/sources.list

RUN apt update -oAcquire::AllowInsecureRepositories=true && apt install -y --allow-unauthenticated deb-multimedia-keyring && apt update && apt upgrade -y
RUN apt install -y python3 python3-dev python3-pip python3-venv npm libsm-dev libxrender-dev libxext-dev libffi-dev

RUN pip3 install flask uwsgi pillow numpy scipy blinker wheel numpy scipy matplotlib scikit-image scikit-learn  

RUN apt -y install build-essential checkinstall cmake pkg-config yasm git libjpeg-dev libpng-dev libtiff-dev libavcodec-dev libavformat-dev libswscale-dev libavresample-dev libdc1394-22-dev libxine2-dev libv4l-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-rtsp gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-alsa libtbb-dev libgoogle-glog-dev libgflags-dev libgphoto2-dev libeigen3-dev libhdf5-dev python3-dev python3-pip python3-venv unzip wget x264 x265 libx264-dev libx265-dev libgtk-3-dev


RUN wget https://github.com/opencv/opencv/archive/master.zip -O /tmp/opencv.zip && \
    wget https://github.com/opencv/opencv_contrib/archive/master.zip -O /tmp/opencv_contrib.zip && \
    unzip /tmp/opencv.zip -d /tmp && \
    unzip /tmp/opencv_contrib.zip -d /tmp && \
    mkdir -p /tmp/opencv-master/build && \
    cd /tmp/opencv-master/build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D OPENCV_EXTRA_MODULES_PATH=/tmp/opencv_contrib-master/modules .. && \
    make -j$(nproc) && \
    make install && \
    rm -rf /tmp/opencv* && \
    cd

COPY . /app
WORKDIR /app

RUN python3 setup.py develop
RUN npm install --prefix nokkhum/web/static
RUN cd /app/khreng/web/static/brython; for i in $(ls -d */); do python3 -m brython --make_package ${i%%/}; done

ENV NOKKHUM_SETTINGS=/app/nokkhum-production.cfg

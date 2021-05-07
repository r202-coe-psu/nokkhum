#!/bin/bash

apt-get -y install build-essential checkinstall cmake pkg-config yasm git libjpeg-dev libpng-dev libtiff-dev libavcodec-dev libavformat-dev libswscale-dev libavresample-dev libdc1394-22-dev libxine2-dev libv4l-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-rtsp gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-alsa libtbb-dev libgoogle-glog-dev libgflags-dev libgphoto2-dev libeigen3-dev libhdf5-dev python3-dev libx264-dev python3-pip python3-venv unzip wget

pip3 install numpy wheel numpy scipy matplotlib scikit-image scikit-learn  
# pip3 uninstall -y opencv-python
# git clone https://github.com/opencv/opencv.git
# git clone https://github.com/opencv/opencv_contrib.git
wget https://github.com/opencv/opencv/archive/master.zip -O opencv.zip
wget https://github.com/opencv/opencv_contrib/archive/master.zip -O opencv_contrib.zip

unzip opencv.zip
unzip opencv_contrib.zip

mkdir -p opencv-master/build
cd opencv-master/build

cmake -D CMAKE_BUILD_TYPE=RELEASE -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-master/modules ..
make -j$(nproc)
make install

cd ../..
rm -rf opencv*

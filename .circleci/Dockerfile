FROM circleci/python:2.7
MAINTAINER Kitware, Inc. <kitware@kitware.com>

# Install Node.js 6
RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash - \
  && sudo apt-get install -y nodejs \
  && sudo npm install -g npm

# Install Girder (including all plugins) system prereqs
RUN sudo apt-get update && sudo apt-get install -y \
    libpython-dev \
    libldap2-dev \
    libsasl2-dev

# Install Girder development prereqs
RUN sudo mkdir --parents "/opt/cmake" \
  && curl --location "http://cmake.org/files/v3.4/cmake-3.4.3-Linux-x86_64.tar.gz" | \
    gunzip --stdout | \
    sudo tar --extract --directory "/opt/cmake" --strip-components 1 \
  && sudo ln --symbolic --force "/opt/cmake/bin/cmake" "/usr/local/bin/cmake" \
  && sudo ln --symbolic --force "/opt/cmake/bin/ctest" "/usr/local/bin/ctest"

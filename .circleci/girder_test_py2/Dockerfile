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
# CMake < 3.1 does not install properly from binaries, so fetch 3.0 from packages
RUN sudo apt-get update && sudo apt-get install -y \
    cmake

#!/bin/bash
# Note we assume sudo apt update && sudo apt upgrade has been run
# Autohotspot needs to be installed with the interactive installer

# install apt dependencies
sudo apt install python3 python3-pip git mosquitto mosquitto-clients pigpio python3-picamera -y -qq

# install python3 dependencies
sudo pip3 install paho-mqtt pigpio adafruit-circuitpython-bmp280

# enable services on startup
sudo systemctl enable mosquitto
sudo systemctl enable pigpiod

# enable remote gpio and IC2
sudo raspi-config nonint do_rgpio 0
sudo raspi-config nonint do_i2c 0

# download flight software and install
sudo curl https://raw.githubusercontent.com/rendermaniac/wbrpi/main/flight_computer3.py -o /usr/bin/flight_computer3.py

# add flight_computer3.py to /etc/rc.local just before exit 0 command
sudo sed -i.bak -e '$ipython3 \/usr\/bin\/flight_computer3.py&' /etc/rc.local

# download autohotspot
curl "https://www.raspberryconnect.com/images/hsinstaller/AutoHotspot-Setup.tar.gz" -o AutoHotspot-Setup.tar.gz
tar -xzvf AutoHotspot-Setup.tar.gz
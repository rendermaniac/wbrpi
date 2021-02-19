# Note we assume sudo apt update && sudo apt upgrade has been run
# Enabling IC2 and remote GPIO needs to be done manually with raspi-config

# Autohotspot needs to be installed with the interactive installer

# install apt dependencies
sudo apt install python3 python3-pip git mosquitto mosquitto-clients pigpio -y -qq

# install python3 dependencies
sudo pip3 install paho-mqtt pigpio adafruit-circuitpython-bmp280

# enable services on startup
sudo systemctl enable mosquitto
sudo systemctl enable pigpiod

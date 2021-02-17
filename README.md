# Raspberry Pi based flight logging software

# Raspberry Pi setup

Install Raspberry Pi Lite using the Pi Imager tool:

https://www.raspberrypi.org/blog/raspberry-pi-imager-imaging-utility/

Enable ssh and WiFi:

https://core-electronics.com.au/tutorials/raspberry-pi-zerow-headless-wifi-setup.html

Update Raspberry Pi OS by running:

sudo apt-get update && sudo apt-get upgrade

# Networking

Enable USB OTG (On The Go) connection. This lets you log in via ethernet if you break the wifi configuration! Note that you need Bonjour installed on Windows for this to work:

https://gist.github.com/gbaman/975e2db164b3ca2b51ae11e45e8fd40a

Setting up switching to a hotspot when out of network range. Note that the auto install script seemed to have trouble picking up AU as a country code. I also change the IP address to the same as the network so that I do not need to change between them in tools. Also this appears to disable OTG connection:

https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/158-raspberry-pi-auto-wifi-hotspot-switch-direct-connection

Networking is hard! You will definitly need to re-image your SD card multiple times!

## Apt Requirements

https://pimylifeup.com/raspberry-pi-mosquitto-mqtt-server/

mosquitto
mosquitto-clients

python3
python3-pip

https://gpiozero.readthedocs.io/en/stable/remote_gpio.html

pigpio

## Python Requirements

http://www.steves-internet-guide.com/mqtt-python-beginners-course/

paho-mqtt

gpiozero
pigpio




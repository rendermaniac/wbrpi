# Raspberry Pi setup

Install Raspberry Pi Lite using the Pi Imager tool:

https://www.raspberrypi.org/blog/raspberry-pi-imager-imaging-utility/

Enable ssh and WiFi:

https://core-electronics.com.au/tutorials/raspberry-pi-zerow-headless-wifi-setup.html

Update Raspberry Pi OS by running:

`sudo apt update && sudo apt upgrade`

# Networking

Enable USB OTG (On The Go) connection. This lets you log in via ethernet if you break the wifi configuration! Note that you need Bonjour installed on Windows for this to work:

https://gist.github.com/gbaman/975e2db164b3ca2b51ae11e45e8fd40a

Setting up switching to a hotspot when out of network range. Note that the auto install script seemed to have trouble picking up AU as a country code. I also change the IP address to the same as the network so that I do not need to change between them in tools. Also this appears to disable OTG connection:

https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/183-raspberry-pi-automatic-hotspot-and-static-hotspot-installer

From the installer choose option 2 to allow auto hotspot switching without internet on the device. The Wifi device on the Raspberry Pi Zero W can bridge a wifi network so you can have internet. However it gets really confused when the Wifi network isn't there and performance drops off to a crawl.

I set up the hotspot IP address to be the same as the static IP on my local network. This should give a seamless transition 

Networking is hard! You will definitly need to re-image your SD card multiple times! I have been using win32 Disk Imager to backup the SD card so I can go back to a known good state:

https://sourceforge.net/projects/win32diskimager/

# Development

Install Python 3 so that we can run Python code

`sudo apt install python3 python3-pip`

It's also a good idea to install git to that we can clone / save code to github

`sudo apt install git`

# Communicating with the Android app

Install the Mosquitto MQQT server so that we can easily communicate with our dashboard

`sudo apt install mosquitto mosquitto-clients`

https://pimylifeup.com/raspberry-pi-mosquitto-mqtt-server/

We can then enable Mosquitto on startup using:

`sudo systemctl enable mosquitto`

The Android app I am using is Dash MQQT https://play.google.com/store/apps/details?id=net.routix.mqttdash&hl=en_US&gl=US

We then install the Python library to send and recieve MQQT topic data

`sudo pip3 install paho-mqtt`
  
There is some general information on using MQQT from Python here:

http://www.steves-internet-guide.com/mqtt-python-beginners-course/

# Reading Altitude

Firstly we need to follow this guide to install Adafruit CircuitPython with Blinka (the Micropython compatibility layer for Linux)

Luckily if we install the BMP280 pressure sensor driver using pip3, it will install all the requirements for us:

`sudo pip3 install adafruit-circuitpython-bmp280`

Note that IC2 needs to be enabled by running:

`sudo raspi-config`
  
Then choosing option:

`3 Interface Options > P5 IC2`

# Driving servos

The servos are driven by PiGPIO. We use a Python library to talk to a daemon - which actually sends the PWM signals to the servo. The Raspberry Pi Zero W has 2 hardware PWM channels. Use one of these if you can as software can have timing issues.

https://gpiozero.readthedocs.io/en/stable/remote_gpio.html

`sudo apt install pigpio`

And enable it to run at boot:

`sudo systemctl enable pigpiod`

Note that Remote GPIO needs to be enabled by running:

`sudo raspi-config`
  
Then choosing option:

`3 Interface Options > P8 Remote GPIO`

The Python library can be istalled with

`sudo pip3 install pigpio`

# Get the flight software

Download the flight computer script from github:

`git clone https://github.com/rendermaniac/wbrpi`

The easiest way to get it to run on startup is to add it to the /etc/rc.local file before `exit 0`. I may looking into a fancy systemctl way of doing this in the future as rc.local is being depreciated. Note that anything in rc.local will get run as root.

# Reporting

Install InfluxDB

https://pimylifeup.com/raspberry-pi-influxdb/

Setup InfluxDB with Python

https://diyi0t.com/visualize-mqtt-data-with-influxdb-and-grafana/

# Quick install

Most of these operations can be automated by running these commands on a fresh Raspberry Pi OS install:

```
 curl https://raw.githubusercontent.com/rendermaniac/wbrpi/main/autorocket.sh -o autorocket.sh
 ./autorocket.sh
```

Note that this has no checks, backups or any way to restore the previous state. Only run on a Raspberry Pi install you really don't care about! I have only tested this on my machine.

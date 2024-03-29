import time
import board
import Adafruit_BMP.BMP085 as BMP085

I2C = board.I2C()  # uses board.SCL and board.SDA
sensor = BMP085.BMP085()

while True:

    print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))
    print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()))
    print('Altitude = {0:0.2f} m'.format(sensor.read_altitude()))
    print('Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure()))

    time.sleep(1)

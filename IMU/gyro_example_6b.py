import time
import board
import adafruit_l3gd20

I2C = board.I2C()  # uses board.SCL and board.SDA
gyro_sensor = adafruit_l3gd20.L3GD20_I2C(I2C, address=0x6b)

while True:
    print("Angular Velocity (rad/s): {}".format(gyro_sensor.gyro))
    time.sleep(1)

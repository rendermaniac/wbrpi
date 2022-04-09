import time
import board
from lsm303d import LSM303D

I2C = board.I2C()  # uses board.SCL and board.SDA
lsm = LSM303D(0x1e)

while True:
    xyz = lsm.accelerometer()
    print(("accel: {:+06.2f}g : {:+06.2f}g : {:+06.2f}g").format(*xyz))
    time.sleep(1)

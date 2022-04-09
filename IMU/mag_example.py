import time
import board
from lsm303d import LSM303D

I2C = board.I2C()  # uses board.SCL and board.SDA
lsm = LSM303D(0x1e)

while True:
    xyz = lsm.magnetometer()
    print(("mag: {:+06.2f} : {:+06.2f} : {:+06.2f}").format(*xyz))

    time.sleep(1)

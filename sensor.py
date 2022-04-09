import logging

import busio
import board
import adafruit_l3gd20
import lsm303d
import Adafruit_BMP.BMP085 as BMP085
import psutil
import csv

class Sensor(object):

    def __init__(self, simulatefile=None):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.accel_sensor = lsm303d.LSM303D(0x1e)
        self.gyro_sensor = adafruit_l3gd20.L3GD20_I2C(i2c, address=0x6a)
        self.pressure_sensor = BMP085.BMP085()

        self.fields = [ "accelx", "accely", "accelz",
                        "magnetx", "magnety", "magnetz",
                        "rotatex", "rotatey", "rotatez",
                        "altitude", "temperature", "pressure",
                        "cpu", "memory"]

        self.simulatefile = simulatefile
        self.simhandle = None
        self.simdata = None
        if self.simulatefile:
            self.simhandle = open(self.simulatefile, "r", newline="")
            logging.warning("SIMULATION MODE")

        self.reset()

    def reset(self):

        if self.simulatefile:
            self.simhandle.seek(0)
            # we need to recreate the csv object or we start reading the headers
            self.simdata = csv.DictReader(self.simhandle)

        self.set_sealevel()
        self.altitude_max = 0.0
        self.altitude_diff = 0.0

    def set_sealevel(self):
        self.sea_level_pressure = self.pressure_sensor.read_pressure()

    @property
    def altitude(self):
        alt = self.pressure_sensor.read_altitude( sealevel_pa=self.sea_level_pressure)

        if self.simdata:
            try:
                row = next(self.simdata)
                alt = float(row["altitude"])
                logging.debug(f"Simulated")
            except StopIteration:
                logging.debug(f"End of simulation file")
                self.reset()

        self.altitude_max = max(alt, self.altitude_max)
        self.altitude_diff = self.altitude_max - alt
        return alt

    @property
    def acceleration(self):
        return self.accel_sensor.accelerometer()

    @property
    def magnetic_field(self):
        return self.accel_sensor.magnetometer()

    @property
    def rotation(self):
        return self.gyro_sensor.gyro

    @property
    def temperature(self):
        return self.pressure_sensor.read_temperature()

    @property
    def pressure(self):
        return self.pressure_sensor.read_pressure()

    @property
    def cpu(self):
        return psutil.cpu_percent()

    @property
    def memory(self):
        return psutil.virtual_memory().percent

    def as_dict(self):
        rowdata = {}
        accel = self.acceleration
        rowdata["acceleration_x"] = accel[0]
        rowdata["acceleration_y"] = accel[1]
        rowdata["acceleration_x"] = accel[2]
        magnet = self.magnetic_field
        rowdata["magnetic_field_x"] = magnet[0]
        rowdata["magnetic_field_y"] = magnet[1]
        rowdata["magnetic_field_z"] = magnet[2]
        rotate = self.rotation
        rowdata["rotation_x"] = rotate[0]
        rowdata["rotation_y"] = rotate[1]
        rowdata["rotation_z"] = rotate[2]
        rowdata["altitude"] = self.altitude
        rowdata["temperature"] = self.temperature
        rowdata["pressure"] = self.pressure
        rowdata["cpu"] = self.cpu
        rowdata["memory"] = self.memory
        return rowdata

import logging

import busio
import board
import adafruit_bmp280
import psutil
import csv

class Sensor(object):

    def __init__(self, simulatefile=None):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

        self.fields = ["altitude", "temperature", "pressure", "cpu", "memory"]

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
        self.bmp280.sea_level_pressure = self.bmp280.pressure

    @property
    def altitude(self):
        alt = self.bmp280.altitude

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
    def temperature(self):
        return self.bmp280.temperature

    @property
    def pressure(self):
        return self.bmp280.pressure

    @property
    def cpu(self):
        return psutil.cpu_percent()

    @property
    def memory(self):
        return psutil.virtual_memory().percent

    def as_dict(self):
        rowdata = {}
        rowdata["altitude"] = self.altitude
        rowdata["temperature"] = self.temperature
        rowdata["pressure"] = self.pressure
        rowdata["cpu"] = self.cpu
        rowdata["memory"] = self.memory
        return rowdata

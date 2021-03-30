import logging

class State(object):

    LAUNCHPAD_READY = 0
    APOGEE = 1
    LANDED = 2

    def __init__(self, sensor):
        self.DROP_AFTER_APOGEE = 5.0
        self.sensor = sensor
        self.fields = ["state"]
        self.reset()

    def reset(self):
        self.state = self.LAUNCHPAD_READY

    def calculate(self):

        if (self.sensor.altitude_diff > self.DROP_AFTER_APOGEE):
            self.state = self.APOGEE

    def at_apogee(self):
        return self.state == self.APOGEE

    def as_dict(self):
        return {"state" : self.state}

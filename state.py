import logging

class State(object):

    LAUNCHPAD_READY = 0
    APOGEE = 1
    LANDED = 2

    def __init__(self):
        self.DROP_AFTER_APOGEE = 5.0
        self.fields = ["state"]
        self.reset()

    def reset(self):
        self.state = self.LAUNCHPAD_READY

    def calculate(self, sensor):

        if (sensor.altitude_diff > self.DROP_AFTER_APOGEE):
            self.state = self.APOGEE

    def as_dict(self):
        return {"state" : self.state}

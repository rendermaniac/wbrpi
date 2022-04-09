import time
import logging
import argparse

from .mqtt import Mqtt

from .sensor import Sensor
from .state import State
from .recorder import Recorder
from .parachute import Parachute

class Rocket(object):

    def __init__(self, simulate=None):     
        self.sensor = Sensor(simulate)
        self.state = State(self.sensor)
        self.parachute = Parachute()
        self.recorder = Recorder([self.sensor, self.parachute])

        self.delay = 1.0

        self.monitor = Mqtt(self)

        # self test and running indicator
        self.parachute.deploy()
        time.sleep(1.0)
        self.parachute.reset()

        #self.parachute_autodeploy(True)

        logging.info("Running flight computer")

    def reset(self):
        self.sensor.reset()
        self.state.reset()
        self.parachute.reset()
        self.monitor.reset()
        self.recorder.reset()
        logging.info("Reset Rocket")

    def record(self, state):
        if state:
            self.delay = 0.1
            self.recorder.start_recording()
        else:
            self.delay = 1.0
            self.recorder.stop_recording()
            self.monitor.post_record(self.recorder)

    def run(self):

        while True:

            if self.recorder.recording:
                self.state.calculate()
                self.recorder.record_data()

                # auto deploy parachute
                if self.parachute.autodeploy and not self.parachute.deployed and self.state.at_apogee():
                    self.parachute.deploy()
                    self.recorder.take_apogee_snapshot()
                    self.monitor.parachute_deployed()
                    logging.info(f"auto deploying parachute at height {self.sensor.altitude}")
            
            logging.debug(f"Reading altitude {self.sensor.altitude} max altitude: {self.sensor.altitude_max}")
            self.monitor.send_data(self.sensor)

            time.sleep(self.delay)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", type=str, help="pass a simulation csv file instead of live readings")
    args = parser.parse_args()

    rocket = Rocket(simulate=args.simulate)
    rocket.run()

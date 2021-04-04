import os.path
import time
import logging
import argparse

from paho.mqtt import client as mqtt_client

from .sensor import Sensor
from .state import State
from .recorder import Recorder
from .parachute import Parachute

def on_message(client, rocket, msg):
    payload = msg.payload.decode()
    if msg.topic == "/rocket/telemetry/reset":
        rocket.reset()
    elif msg.topic == "/rocket/telemetry/notes":
        rocket.recorder.set_notes(payload)
    elif msg.topic == "/rocket/camera/enable":
        rocket.recorder.enable_camera(int(payload))
    elif msg.topic == "/rocket/camera/options":
        if payload == "hd":
            rocket.recorder.set_camera_hd()
        elif payload == "slowmo":
            rocket.recorder.set_camera_slow_motion()
    elif msg.topic == "/rocket/telemetry/record":
        rocket.record(int(payload))
    elif msg.topic == "/rocket/parachute/deploy":
        if payload == "1" and rocket.parachute.deployed == False:
            rocket.parachute.deploy()
            rocket.client.publish("/rocket/parachute/deploy", "1")
        elif payload == "0" and rocket.parachute.deployed == True:
            rocket.parachute.reset()
            rocket.client.publish("/rocket/parachute/deploy", "0")
    elif msg.topic == "/rocket/parachute/auto":
        rocket.parachute.auto_deploy(int(payload))

class Rocket(object):

    def __init__(self, simulate=None):     
        self.sensor = Sensor(simulate)
        self.state = State(self.sensor)
        self.parachute = Parachute()
        self.recorder = Recorder([self.sensor, self.parachute])

        self.delay = 1.0

        self.client = mqtt_client.Client("flight_computer", userdata=self)
        self.client.connect("127.0.0.1", 1883)

        self.client.subscribe("/rocket/telemetry/reset")
        self.client.subscribe("/rocket/telemetry/record")
        self.client.subscribe("/rocket/telemetry/notes")

        self.client.subscribe("/rocket/camera/enable")
        self.client.subscribe("/rocket/camera/options")

        self.client.subscribe("/rocket/parachute/deploy")
        self.client.subscribe("/rocket/parachute/auto")
        self.client.subscribe("/rocket/parachute/reset")

        self.client.on_message = on_message
        self.client.loop_start()

        self.client.publish("/rocket/telemetry/record", "0")
        self.client.publish("/rocket/telemetry/notes", "")
        self.client.publish("/rocket/parachute/deploy", "0")
        self.client.publish("/rocket/parachute/auto", "1")
        self.client.publish("/rocket/camera/enable", "1")
        self.client.publish("/rocket/camera/options", "slowmo")

        # self test and running indicator
        self.parachute.deploy()
        time.sleep(1.0)
        self.parachute.reset()

        self.client.publish("/rocket/parachute/auto", "1")

        #self.parachute_autodeploy(True)

        logging.info("Running flight computer")

    def reset(self):
        self.sensor.reset()
        self.client.publish("/rocket/telemetry/altitude", self.sensor.altitude)
        self.client.publish("/rocket/telemetry/altitude/max", self.sensor.altitude_max)

        self.state.reset()

        self.parachute.reset()
        self.client.publish("/rocket/parachute/deploy", "0")

        self.recorder.reset()

        logging.info("Reset Rocket")

    def send_image(self, topic, image):
        if image and os.path.exists(image):
            f = open(image, "rb")
            data = f.read()
            self.client.publish(topic, bytearray(data))

    def record(self, state):
        if state:
            self.delay = 0.1
            self.recorder.start_recording()
        else:
            self.delay = 1.0
            self.recorder.stop_recording()
            self.send_image("/rocket/camera/apogee", self.recorder.apogee_file)
            self.send_image("/rocket/telemetry/plot", self.recorder.plot_file)
            self.send_image("/rocket/telemetry/plot/accumulated", self.recorder.plot_file_accumulated)

    def run(self):

        while True:

            if self.recorder.recording:
                self.state.calculate()
                self.recorder.record_data()

                # auto deploy parachute
                if self.parachute.autodeploy and not self.parachute.deployed and self.state.at_apogee():
                    self.parachute.deploy()
                    self.recorder.take_apogee_snapshot()
                    self.client.publish("/rocket/parachute/deploy", "1")
                    logging.info(f"auto deploying parachute at height {self.sensor.altitude}")
                

            logging.debug(f"Reading altitude {self.sensor.altitude} max altitude: {self.sensor.altitude_max}")
            self.client.publish("/rocket/telemetry/altitude", self.sensor.altitude)
            self.client.publish("/rocket/telemetry/altitude/max", self.sensor.altitude_max)

            time.sleep(self.delay)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", type=str, help="pass a simulation csv file instead of live readings")
    args = parser.parse_args()

    rocket = Rocket(simulate=args.simulate)
    rocket.run()

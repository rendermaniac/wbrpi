import math
import time
import logging

import argparse
from datetime import datetime

import pigpio

import board
import busio
import adafruit_bmp280

SERVO_PIN = 13
PARACHUTE_DEPLOY = 0
PARACHUTE_RESET = 500

DROP_AFTER_APOGEE = 1.0

from paho.mqtt import client as mqtt_client

def on_message(client, rocket, msg):
    payload = msg.payload.decode()
    if msg.topic == "/rocket/telemetry/reset":
        rocket.reset()
    elif msg.topic == "/rocket/telemetry/record":
        rocket.record(int(payload))
    elif msg.topic == "/rocket/parachute/deploy":
        if payload == "1":
            rocket.parachute_deploy()
        else:
            rocket.parachute_reset()
    elif msg.topic == "/rocket/parachute/auto":
        rocket.set_parachute_auto(int(payload))

class Rocket(object):

    def __init__(self, simulate=None):     
        self.altitude = 0.0
        self.max_altitude = 0.0
        self.recording = False
        self.record_reset = False

        self.simulate = None
        if simulate:
            self.simulate = open(simulate, "r")
            self.simulate.readline() # ignore headers
            logging.warning("SIMULATION MODE")

        self.parachute_deployed = False
        self.parachute_height = 15.0
        self.parachute_autodeploy = True

        self.csvfile = None

        self.client = mqtt_client.Client("flight_computer", userdata=self)
        self.client.connect("127.0.0.1", 1883)

        self.client.subscribe("/rocket/telemetry/reset")
        self.client.subscribe("/rocket/telemetry/record")

        self.client.subscribe("/rocket/parachute/deploy")
        self.client.subscribe("/rocket/parachute/auto")
        self.client.subscribe("/rocket/parachute/reset")

        self.client.on_message = on_message
        self.client.loop_start()

        i2c = busio.I2C(board.SCL, board.SDA)
        self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

        self.pi = pigpio.pi()
        self.pi.set_servo_pulsewidth(SERVO_PIN, PARACHUTE_RESET)

        self.reset()
        logging.info("Running flight computer")

    def reset(self):
        self.altitude = 0.0
        self.max_altitude = 0.0
        self.bmp280.sea_level_pressure = self.bmp280.pressure
        self.client.publish("/rocket/telemetry/altitude", self.altitude)
        self.client.publish("/rocket/telemetry/altitude/max", self.max_altitude)

        if self.simulate:
            self.simulate.seek(0) # reset to start of simulation file
            self.simulate.readline() # ignore headers

        logging.info("Reset Altitude")

        self.parachute_reset()
        self.set_parachute_auto(True)
        self.client.publish("/rocket/parachute/deploy", "0")
        self.client.publish("/rocket/parachute/auto", "1")
        self.client.publish("/rocket/telemetry/record", "0")
        logging.info("Reset Parachute")

    def record(self, state):
        self.recording = bool(state)
        if self.recording:
            if self.csvfile:
                self.csvfile.close()
            today = datetime.now().strftime("%Y_%m_%d_%H_%M")
            self.csvfile = open(f"{today}.csv", "w")
            self.csvfile.write(f"time,altitude,deploy\n") # header
            
        logging.info(f"Set recording to {self.recording}")

    def parachute_deploy(self):
        if not self.parachute_deployed:
            logging.info(f"Deploying parachute")
            self.pi.set_servo_pulsewidth(SERVO_PIN, PARACHUTE_DEPLOY)
            self.client.publish("/rocket/parachute/deploy", "1")
            self.parachute_deployed = True

    def set_parachute_auto(self, state):
        self.parachute_autodeploy = state
        if self.parachute_autodeploy:
            logging.info("Parachute deploy set to auto")
        else:
            logging.info("Parachute deploy set to manual")

    def parachute_reset(self):
        logging.info(f"Reset parachute")
        self.pi.set_servo_pulsewidth(SERVO_PIN, PARACHUTE_RESET)
        self.parachute_deployed = False

    def run(self):

        while True:

            self.altitude = self.bmp280.altitude

            if self.recording:
                
                delay = 0.1
                now = datetime.timestamp(datetime.now())

                # Simulate altititude
                if self.simulate:
                    line = self.simulate.readline()
                    if line != "\n":
                        self.altitude = float(line.split(",")[1])
                        logging.info(f"Simulated")
                    else:
                        self.recording = False # stop recording at end of file
                        self.simulate.seek(0) # reset to start of simulation file
                        self.simulate.readline() # ignore headers

                logging.info(f"Reading altitude {self.altitude}")
                self.csvfile.write(f"{now},{self.altitude},{int(self.parachute_deployed)}\n")
                self.csvfile.flush()

                # auto parachute deploy
                if self.parachute_autodeploy \
                and not self.parachute_deployed \
                and (self.max_altitude - self.altitude) > DROP_AFTER_APOGEE:
                    self.parachute_deploy()
                    logging.info(f"auto deploying parachute at height {self.altitude}")

            else:
                delay = 1

            self.client.publish("/rocket/telemetry/altitude", self.altitude)

            if self.altitude > self.max_altitude:
                self.max_altitude = self.altitude
                self.client.publish("/rocket/telemetry/altitude/max", self.max_altitude)

            time.sleep(delay)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", type=str, help="pass a simulation csv file instead of live readings")
    args = parser.parse_args()

    rocket = Rocket(simulate=args.simulate)
    rocket.run()
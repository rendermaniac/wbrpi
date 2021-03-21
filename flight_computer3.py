import os
import os.path
import math
import time
import logging

import argparse
from datetime import datetime

import pigpio

import board
import busio
import adafruit_bmp280

import picamera

from matplotlib import pyplot as plt

SERVO_PIN = 13
PARACHUTE_DEPLOY = 1500
PARACHUTE_RESET = 500

DROP_AFTER_APOGEE = 5.0

TELEMETRY_PATH = "/home/pi/"

from paho.mqtt import client as mqtt_client

def on_message(client, rocket, msg):
    payload = msg.payload.decode()
    if msg.topic == "/rocket/telemetry/reset":
        rocket.reset()
    elif msg.topic == "/rocket/telemetry/notes":
        rocket.set_notes(payload)
    elif msg.topic == "/rocket/camera/enable":
        rocket.enable_camera(int(payload))
    elif msg.topic == "/rocket/camera/options":
        if payload == "hd":
            rocket.set_camera_hd()
        elif payload == "slowmo":
            rocket.set_camera_slow_motion()
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
        self.altitudes = []
        self.parachute_deploys = []
        self.camera_record = False
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

        self.filename = None
        self.notes = None
        self.csvfile = None

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

        i2c = busio.I2C(board.SCL, board.SDA)
        self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

        self.pi = pigpio.pi()
        self.pi.set_servo_pulsewidth(SERVO_PIN, PARACHUTE_RESET)

        self.camera = picamera.PiCamera()
        self.set_camera_hd()
        self.client.publish("/rocket/camera/options", "hd")

        self.reset()

        self.client.publish("/rocket/parachute/auto", "1")
        self.client.publish("/rocket/camera/enable", "0")

        logging.info("Running flight computer")

    def reset_data(self):
        self.altitude = 0.0
        self.max_altitude = 0.0
        self.altitudes = []
        self.parachute_deploys = []
        self.bmp280.sea_level_pressure = self.bmp280.pressure

    def reset(self):
        self.reset_data()

        self.client.publish("/rocket/telemetry/altitude", self.altitude)
        self.client.publish("/rocket/telemetry/altitude/max", self.max_altitude)

        logging.info("Reset Altitude")

        self.parachute_reset()
        self.client.publish("/rocket/telemetry/record", "0")
        logging.info("Reset Parachute")

    def set_notes(self, notes):
        self.notes = notes
        logging.info(f"Set notes: {self.notes}")

    def enable_camera(self, enable):
        self.camera_record = enable
        logging.info(f"Camera recording: {self.camera_record}")

    def set_camera_hd(self):
        self.camera.resolution = (1920, 1080)
        self.camera.framerate = 30
        logging.info(f"Camera set to HD")

    def set_camera_slow_motion(self):
        self.camera.resolution = (640, 480)
        self.camera.framerate = 90
        logging.info(f"Camera set to slow motion")

    def record(self, state):
        self.recording = bool(state)
        if self.recording:
            self.reset_data()
            self.filename = datetime.now().strftime("%Y_%m_%d_%H_%M")
            self.csvfile = open(f"{TELEMETRY_PATH}{self.filename}.csv", "w")

            if self.notes:
                self.csvfile.write(f"{self.notes}\n")

            self.csvfile.write("time,altitude,deploy\n") # header

            if self.camera_record:
                self.camera.start_recording(f"{TELEMETRY_PATH}{self.filename}.h264")        
        else:
            if self.csvfile:
                self.csvfile.close()

            if self.camera_record:
                if self.camera.recording:
                    self.camera.stop_recording()

            # cleanup
            apogee_file = f"{TELEMETRY_PATH}{self.filename}.jpg"
            if os.path.exists(apogee_file):
                f = open(apogee_file, "rb")
                apogee_data = f.read()
                self.client.publish("/rocket/camera/apogee", bytearray(apogee_data))

            plot_file = f"{TELEMETRY_PATH}{self.filename}.png"
            plt.plot(self.altitudes, label="Altitude")
            plt.plot(self.parachute_deploys, label="Parachute Deploy")
            plt.title("Pi High Rockets")
            plt.savefig(plot_file)

            f = open(plot_file, "rb")
            plot_data = f.read()
            self.client.publish("/rocket/telemetry/plot", bytearray(plot_data))

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
                # TODO switch to using the csv library
                if self.simulate:
                    line = self.simulate.readline()
                    if line and line != "\n":
                        simdata = line.split(",")
                        if simdata:
                            self.altitude = float(simdata[1])
                            #self.parachute_deployed = float(simdata[2])
                        logging.info(f"Simulated")
                    else:
                        logging.info(f"End of simulation file")
                        self.simulate.seek(0) # reset to start of simulation file
                        self.simulate.readline() # ignore headers

                if not self.csvfile.closed:
                    self.csvfile.write(f"{now},{self.altitude},{int(self.parachute_deployed)}\n")
                    self.csvfile.flush()
                    self.altitudes.append(self.altitude)
                    self.parachute_deploys.append(self.parachute_deployed)
                
                # auto parachute deploy
                if self.parachute_autodeploy \
                and not self.parachute_deployed \
                and (self.max_altitude - self.altitude) > DROP_AFTER_APOGEE:
                    self.parachute_deploy()

                    # take photo at apogee
                    if self.camera_record:
                        self.camera.capture(f"{TELEMETRY_PATH}{self.filename}.jpg", use_video_port=True)
                        logging.info("Taking apogee photo")

                    logging.info(f"auto deploying parachute at height {self.altitude}")

            else:
                delay = 1.0

            logging.info(f"Reading altitude {self.altitude}")
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
import math
import time
import logging

from datetime import datetime

import pigpio

import board
import busio
import adafruit_bmp280

SERVO_PIN = 13
PARACHUTE_DEPLOY = 1500
PARACHUTE_RESET = 500


from paho.mqtt import client as mqtt_client

def on_message(client, rocket, msg):
    payload = msg.payload.decode()
    if msg.topic == "/rocket/telemetry/reset":
        rocket.reset()
    elif msg.topic == "/rocket/telemetry/record":
        rocket.record(int(payload))
    elif msg.topic == "/rocket/parachute/arm":
        rocket.parachute_arm(int(payload))
    elif msg.topic == "/rocket/parachute/deploy":
        if payload == "1":
            rocket.parachute_deploy()
        else:
            rocket.parachute_reset()
    elif msg.topic == "/rocket/parachute/height":
        rocket.set_parachute_height(float(payload))

class Rocket(object):

    def __init__(self):     
        self.altitude = 0.0
        self.max_altitude = 0.0
        self.recording = False

        self.parachute_armed = False
        self.parachute_height = 10.0

        self.csvfile = None

        self.client = mqtt_client.Client("flight_computer", userdata=self)
        self.client.connect("127.0.0.1", 1883)

        self.client.subscribe("/rocket/telemetry/reset")
        self.client.subscribe("/rocket/telemetry/record")

        self.client.subscribe("/rocket/parachute/arm")
        self.client.subscribe("/rocket/parachute/height")
        self.client.subscribe("/rocket/parachute/deploy")
        self.client.subscribe("/rocket/parachute/reset")

        self.client.on_message = on_message
        self.client.loop_start()

        i2c = busio.I2C(board.SCL, board.SDA)
        self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
        self.reset()

        self.pi = pigpio.pi()
        self.pi.set_servo_pulsewidth(SERVO_PIN, PARACHUTE_RESET)

        logging.info("Running flight computer")

    def reset(self):
        self.altitude = 0.0
        self.max_altitude = 0.0
        self.bmp280.sea_level_pressure = self.bmp280.pressure

        # reset UI
        self.client.publish("/rocket/parachute/deploy", "0")
        self.client.publish("/rocket/parachute/height", str(self.parachute_height))
        self.client.publish("/rocket/parachute/arm", "0")
        self.client.publish("/rocket/telemetry/record", "0")

        logging.info("Reset")

    def record(self, state):
        self.recording = bool(state)

        if self.recording:
            today = datetime.now().strftime("%Y_%m_%d")
            self.csvfile = open(f"{today}.csv", "a")
        else:
            if self.csvfile:
                self.csvfile.close()
        logging.info(f"Set recording to {self.recording}")

    def parachute_arm(self, arm):
        self.parachute_armed = bool(arm)
        logging.info(f"Armed parachute {self.parachute_armed}")

    def parachute_deploy(self):
        if self.parachute_armed:
            logging.info(f"Deploying parachute")
            self.pi.set_servo_pulsewidth(SERVO_PIN, PARACHUTE_DEPLOY)

    def set_parachute_height(self, height):
        self.parachute_height = height
        logging.info(f"Set parachute deploy height to {self.parachute_height}")

    def parachute_reset(self):
        if self.parachute_armed:
            logging.info(f"Reset parachute")
            self.pi.set_servo_pulsewidth(SERVO_PIN, PARACHUTE_RESET)

    def run(self):
        while True:
            self.altitude = self.bmp280.altitude
            now = datetime.timestamp(datetime.now())
            if self.recording:
                self.csvfile.write(f"{now},{self.altitude}\n")
                self.csvfile.flush()

                # auto parachute deploy
                if (self.max_altitude - self.altitude) > 1.0:
                    self.parachute_deploy()

            #self.client.publish("/rocket/telemetry/altitude", self.altitude)

            if self.altitude > self.max_altitude:
                self.max_altitude = self.altitude
                self.client.publish("/rocket/telemetry/altitude/max", self.max_altitude)

            time.sleep(0.2)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    rocket = Rocket()
    rocket.run()
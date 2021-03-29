import logging

import pigpio

class Parachute(object):

    def __init__(self):
        self.deployed = False
        self.autodeploy = True

        self.SERVO_PIN = 13
        self.DEPLOY_PULSEWIDTH = 1500
        self.RESET_PULSEWIDTH = 500

        self.pi = pigpio.pi()
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.RESET_PULSEWIDTH)

        self.fields = ["deployed"]

    def deploy(self):
        if not self.deployed:
            self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.DEPLOY_PULSEWIDTH)
            self.deployed = True
            logging.info(f"Parachute deployed")

    def auto_deploy(self, state):
        self.autodeploy = state
        if self.autodeploy:
            logging.info("Parachute deploy set to auto")
        else:
            logging.info("Parachute deploy set to manual")

    def reset(self):
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, self.RESET_PULSEWIDTH)
        self.deployed = False
        logging.info(f"Reset parachute")

    def check_auto_deploy(self, sensor, state):
        if self.autodeploy and not self.deployed and state.state == state.APOGEE:
            self.deploy()
            logging.info(f"auto deploying parachute at height {sensor.altitude}")

    def as_dict(self):
        return {"deployed" : int(self.deployed)}
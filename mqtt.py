
import os.path
from paho.mqtt import client as mqtt_client

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
            client.publish("/rocket/parachute/deploy", "1")
        elif payload == "0" and rocket.parachute.deployed == True:
            rocket.parachute.reset()
            client.publish("/rocket/parachute/deploy", "0")
    elif msg.topic == "/rocket/parachute/auto":
        rocket.parachute.auto_deploy(int(payload))

class Mqtt(object):

    def __init__(self, rocket):
        self.client = mqtt_client.Client("flight_computer", userdata=rocket)
        self.client.connect("127.0.0.1", 1883)

        self.client.subscribe("/rocket/telemetry/reset")
        self.client.subscribe("/rocket/telemetry/record")
        self.client.subscribe("/rocket/telemetry/notes")

        self.client.subscribe("/rocket/camera/enable")
        self.client.subscribe("/rocket/camera/options")

        self.client.subscribe("/rocket/parachute/deploy")
        self.client.subscribe("/rocket/parachute/auto")
        self.client.subscribe("/rocket/parachute/reset")

        # initialize defaults
        self.client.publish("/rocket/telemetry/record", "0")
        self.client.publish("/rocket/telemetry/notes", "")
        self.client.publish("/rocket/parachute/deploy", "0")
        self.client.publish("/rocket/parachute/auto", "1")
        self.client.publish("/rocket/camera/enable", "1")
        self.client.publish("/rocket/camera/options", "slowmo")

        self.client.on_message = on_message
        self.client.loop_start()

    def reset(self):
        self.client.publish("/rocket/telemetry/altitude", "0")
        self.client.publish("/rocket/telemetry/altitude/max", "0")
        self.client.publish("/rocket/parachute/deploy", "0")

    def parachute_deployed(self):
        self.client.publish("/rocket/parachute/deploy", "1")

    def send_image(self, topic, image):
        if image and os.path.exists(image):
            f = open(image, "rb")
            data = f.read()
            self.client.publish(topic, bytearray(data))

    def send_data(self, sensor):
        self.client.publish("/rocket/telemetry/altitude", sensor.altitude)
        self.client.publish("/rocket/telemetry/altitude/max", sensor.altitude_max)

        acceleration = sensor.acceleration
        self.client.publish("/rocket/telemetry/acceleration/x", acceleration[0])
        self.client.publish("/rocket/telemetry/acceleration/y", acceleration[1])
        self.client.publish("/rocket/telemetry/acceleration/z", acceleration[2])

        rotation = sensor.rotation
        self.client.publish("/rocket/telemetry/rotation/x", rotation[0])
        self.client.publish("/rocket/telemetry/rotation/y", rotation[1])
        self.client.publish("/rocket/telemetry/rotation/z", rotation[2])

    def post_record(self, recorder):
        self.send_image("/rocket/camera/apogee", recorder.apogee_file)
        self.send_image("/rocket/telemetry/plot", recorder.plot_file)
        self.send_image("/rocket/telemetry/plot/accumulated", recorder.plot_file_accumulated)
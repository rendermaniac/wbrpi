import random
import time
from paho.mqtt import client as mqtt_client

client = mqtt_client.Client("heartbeat")
client.connect("127.0.0.1", 1883)

client.loop_start()

while True:
    client.publish("/beacon/heartbeat", random.random())
    time.sleep(1.0)
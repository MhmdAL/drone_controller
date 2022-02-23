import threading
import json
import paho.mqtt.client as mqtt

client = mqtt.Client('drone_station2')
client.connect('broker.emqx.io', 1883, 60)

txt = input('enter something\n')

client.publish("drone-location-request", txt)
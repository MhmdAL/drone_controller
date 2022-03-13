from utils import log
import json
import threading
import os
import paho.mqtt.client as mqtt
import station_state as State
from Event import *

BROKER_URL = os.environ.get("BROKER_URL", 'broker.emqx.io')

on_land_request = Event()
on_start_mission_request = Event()
on_drone_location_request = Event()
on_station_update_request = Event()

def init():
    global client; client = mqtt.Client('drone_station_{}'.format(State.station_id))

    client.connect(BROKER_URL, 1883, 60)
    client.subscribe("land-request")
    client.subscribe("start-mission-request")
    client.subscribe("drone-location-request")
    client.subscribe(f"station-update-{State.station_id}-request")

    client.on_message = on_message_handler

def start():
    client.loop_forever()

def on_message(client, userdata, message):
    log('received message from topic {}'.format(message.topic))
    data = json.loads(message.payload.decode('utf-8'))
    if(message.topic == 'drone-location-request'):
        on_drone_location_request(data)
    elif(message.topic == 'start-mission-request'):
        on_start_mission_request(data)
    elif(message.topic == 'station-update-{}-request'.format(State.station_id)):
        on_station_update_request(data)
    elif(message.topic == 'land-request'):
        on_land_request(data)

def on_message_handler(client, userdata, message):
    t = threading.Thread(target = on_message, args = (client, userdata, message))
    t.start()

def publish_message(topic, data):
    client.publish(topic, data)
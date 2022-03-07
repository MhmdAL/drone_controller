from concurrent.futures import thread
import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged, GpsLocationChanged
from olympe.messages.ardrone3.GPSSettingsState import HomeChanged
from olympe.messages.common.MavlinkState import MavlinkFilePlayingStateChanged
from olympe.messages.drone_manager import connection_state
from olympe.messages.common.Mavlink import Start
from olympe.messages.common.Common import AllStates
from logging import exception
from typing import List, Dict
import time
import math
import threading
from threading import Timer
import requests
import json
import os
import socket
import sys
import paho.mqtt.client as mqtt
import schedule
from models import Point
from utils import init_logger, log
import serial
import adafruit_fingerprint

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

olympe.log.update_config({"loggers": {"olympe": {"level": "INFO"}}})

BROKER_URL = os.environ.get("BROKER_URL", 'broker.emqx.io')
DRONE_IP = os.environ.get("DRONE_IP", "192.168.42.1")
DRONE_ID = os.environ.get('DRONE_ID')

drone = olympe.Drone(DRONE_IP)

station_id = None

expected_fpid = None
expected_rfid = None
station_type = None

client = None

listener = None

def get_fingerprint():
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

def try_connect():
    if drone.connected:
        return True
    
    log ('retrying connection to drone..')

    global listener; 
    if listener != None:
        listener.unsubscribe()

    listener = FlightListener(drone)
    listener.subscribe()

    print('Connected? {}'.format(drone.connected))

    is_connected = drone.connect()
    if is_connected:
        print('connected')

    return is_connected

def run_schedule():
    while(True):
        schedule.run_pending()
        time.sleep(1)

def init():
    global station_id; station_id = sys.argv[1]

    init_logger(station_id)

    global client; client = mqtt.Client('drone_station_{}'.format(station_id))

    schedule.every(1).seconds.do(try_connect)

    scheduler_task = threading.Thread(target = run_schedule)
    scheduler_task.start()

    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Fingerprint templates: ", finger.templates)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Number of templates found: ", finger.template_count)
    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to get system parameters")
    
    client.connect(BROKER_URL, 1883, 60)

    client.subscribe("land-request")
    client.subscribe("start-mission-request")
    client.subscribe("drone-location-request")

    client.on_message = on_message_handler

    client.loop_forever()

def get_drone_position():
    res = drone.get_state(HomeChanged)

    log('lat: {}, lng: {}, alt: {}'.format(res['latitude'], res['longitude'], res['altitude']))

    return (res['latitude'], res['longitude'], res['altitude'])

def upload_flight_plan(bytes):
    log('uploading flight plan')
    res = requests.put(f'http://{DRONE_IP}/api/v1/upload/flightplan', data=bytes, headers={'Content-Type': 'application/octet-stream'})

    return res.json()

def upload_flight_plan_and_start_mission(flight_plan):
    flightPlanUUID = upload_flight_plan(flight_plan)

    assert drone(
        Start(flightPlanUUID, 'flightPlan', _timeout=10000)
    ).wait().success()

def on_drone_location_discovery_request(data):
    log('drone location discovery request received')
    is_connected = try_connect()

    if is_connected:
        client.publish("drone-location-request-ack-event", json.dumps({"station_id": station_id}))

def on_drone_landed():
    log('sending drone landing message')
    client.publish("drone-landed-event", json.dumps({"station_id": station_id}))

def on_flight_mission_completed():
    log('sending flight mission completed message')
    client.publish("flight-mission-completed-event", json.dumps({"station_id": station_id}))

    if get_fingerprint():
        if finger.finger_id == expected_fp_id:
            log('matched fingerprint')
        print("Detected #", finger.finger_id, "with confidence", finger.confidence)
    else:
        print("Finger not found")

def start_mission(data):
    log('[StartMission] - starting mission')

    flight_plan = data['planText'].encode('utf-8')
    log(data['planText'])

    is_connected = try_connect()

    if is_connected:  
        upload_flight_plan_and_start_mission(flight_plan)      
    else:
        log('[StartMission] - could not connect to drone')

def land(data):
    log('[Land] - landing')

    is_connected = try_connect()

    if is_connected:        
        assert drone(
            Landing(_timeout=100)
        ).wait().success()
    else:
        log('[Land] - could not connect to drone')

def handle_station_update(data):
    global expected_fpid; expected_fpid = data.expected_fpid
    global expected_rfid; expected_rfid = data.expected_rfid
    global station_type; station_type = data.station_type
 
def on_message(client, userdata, message):
    log('received message from topic {}'.format(message.topic))
    data = json.loads(message.payload.decode('utf-8'))
    if(message.topic == 'drone-location-request'):
        on_drone_location_discovery_request(data)
    elif(message.topic == 'start-mission-request'):
        start_mission(data)
    elif(message.topic == 'station-update-{}-request'.format(station_id)):
        handle_station_update(data)
    elif(message.topic == 'land-request'):
        land(data)

def on_message_handler(client, userdata, message):
    t = threading.Thread(target = on_message, args = (client, userdata, message))
    t.start()

def print_event(event):
    # Here we're just serializing an event object and truncate the result if necessary
    # before printing it.
    if isinstance(event, olympe.ArsdkMessageEvent):
        max_args_size = 100
        args = str(event.args)
        args = (args[: max_args_size - 3] + "...") if len(args) > max_args_size else args
        
        log("{}({})\n".format(event.message.fullName, args))
    else:
        print(str(event))

class FlightListener(olympe.EventListener):

    @olympe.listen_event(MavlinkFilePlayingStateChanged(_policy = 'wait'))
    def onMavlinkFilePlayingStateChanged(self, event, scheduler):
        print_event(event)
        on_flight_mission_completed()

    @olympe.listen_event(FlyingStateChanged(state = 'landing', _policy = 'wait') >> FlyingStateChanged(state = 'landed', _policy = 'wait'))
    def onFlyingStateChanged(self, event, scheduler):
        print_event(event)
        on_drone_landed()
        
if __name__== "__main__":
    init()
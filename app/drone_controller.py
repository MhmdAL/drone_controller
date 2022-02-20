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

olympe.log.update_config({"loggers": {"olympe": {"level": "INFO"}}})

BROKER_URL = os.environ.get("BROKER_URL", 'broker.emqx.io')
DRONE_IP = os.environ.get("DRONE_IP", "10.202.0.1")
DRONE_ID = os.environ.get('DRONE_ID')

drone = olympe.Drone(DRONE_IP)

station_id = None

client = None

listener = None

def try_connect():
    log ('retrying connection to drone..')

    with open('/app/droneip{}.txt'.format(station_id)) as f:
        data = f.read()

    global drone

    if not drone._ip_addr_str == data:
        drone.disconnect()
        drone = olympe.Drone(data) #TODO: remove this

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

    schedule.every(10).seconds.do(try_connect)

    scheduler_task = threading.Thread(target = run_schedule)
    scheduler_task.start()
    
    client.connect(BROKER_URL, 1883, 60)

    client.subscribe("mission-request")
    client.subscribe("drone-location-request")

    client.on_message = on_message_handler

    client.loop_forever()

def get_drone_position():
    res = drone.get_state(HomeChanged)

    log('lat: {}, lng: {}, alt: {}'.format(res['latitude'], res['longitude'], res['altitude']))

    return (res['latitude'], res['longitude'], res['altitude'])

def upload_flight_plan(bytes):
    res = requests.put(f'http://{DRONE_IP}/api/v1/upload/flightplan', data=bytes, headers={'Content-Type': 'application/octet-stream'})

    return res.json()

def generate_flight_plan(station1, station2):
    # TODO: this should retreive the flight plan from the backend

    # POST http://mcu/misson/generateplan (cur, dest)

    plan_name = "plan1.txt"

    if station1 == 2 and station2 == 4:
        plan_name = 'plan1.txt'
    elif station1 == 6 and station2 == 4:
        plan_name = 'plan1.txt'
    if station1 == 2 and station2 == 6:
        plan_name = 'plan2.txt'
    elif station1 == 4 and station2 == 6:
        plan_name = 'plan2.txt'
    if station1 == 4 and station2 == 2:
        plan_name = 'plan3.txt'
    elif station1 == 6 and station2 == 2:
        plan_name = 'plan3.txt'

    with open(f'/app/{plan_name}', 'rb') as f:
        plan = f.read()

    return plan

def publish_status_event(status):
    client.publish("mission-status-update", json.dumps({"status": status}))

def on_drone_location_discovery_request(data):
    log('drone location discovery request received')
    is_connected = try_connect()

    drone_pos = get_drone_position()

    if is_connected:
        client.publish("drone-location-request-ack", json.dumps({"station_id": station_id, "current_lat": drone_pos[0], "current_lng": drone_pos[1]}))
        # drone.disconnect()

def on_drone_landed():
    client.publish("drone-landed", json.dumps({"station_id": station_id}))

def start_mission(data):
    log('starting mission')

    print(station_id)

    flight_plan = data['planText'].encode('utf-8')

    is_connected = try_connect()

    if is_connected:
        log('connected to drone - start mission')
        
        flightPlanUUID = upload_flight_plan(flight_plan)

        assert drone(
            Start(flightPlanUUID, 'flightPlan', _timeout=10000)
        ).wait().success()

        log('disconnected from drone - start mission')
        # drone.disconnect()
 
def on_message(client, userdata, message):
    data = json.loads(message.payload.decode('utf-8'))
    if(message.topic == 'drone-location-request'):
        on_drone_location_discovery_request(data)
    elif(message.topic == 'mission-request'):
        start_mission(data)

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

    # @olympe.listen_event(MavlinkFilePlayingStateChanged())
    # def onMavlinkFilePlayingStateChanged(self, event, scheduler):
    #     print_event(event)

    @olympe.listen_event(FlyingStateChanged(state = 'landing') >> FlyingStateChanged(state = 'landed'))
    def onFlyingStateChanged(self, event, scheduler):
        print_event(event)
        on_drone_landed()
        
if __name__== "__main__":
    init()
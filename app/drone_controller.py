from concurrent.futures import thread
import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged, GpsLocationChanged
from olympe.messages.ardrone3.GPSSettingsState import HomeChanged
from olympe.messages.common.MavlinkState import MavlinkFilePlayingStateChanged
from olympe.messages.drone_manager import connection_state
from olympe.messages.common.Mavlink import Start
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

class Point():
    x: float
    y: float

DRONE_IP = "10.202.0.1"

drone_id = os.environ.get('DRONE_ID')
print(f'drone id: {drone_id}')

drone = olympe.Drone(DRONE_IP)

station_id = 2

# def try_connect():
#     print ('retrying connection to drone..')
#     with FlightListener(drone):
#         drone.connect()

# schedule.every(5).seconds.do(try_connect)

# def run_schedule():
#     while(True):
#         schedule.run_pending()
#         time.sleep(1)

# scheduler_task = threading.Thread(target = run_schedule)
# scheduler_task.start()

mission_id = 0
is_executing_mission = False

package_loaded_flag = False
package_received_flag = False

client = mqtt.Client('drone')
client.connect('broker.emqx.io', 1883, 60)
client.subscribe("mission-request")
client.subscribe("mission-continue")
client.subscribe("package-load-ack")
client.subscribe("package-receive-ack")
client.subscribe("drone-location-discovery-request")

def init(station_id):
    pass

def log(message):
    file_object = open('/app/log1', 'a')

    file_object.write(message + '\n')
        
    file_object.close()

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
    client.publish("mission-status-update", json.dumps({"status": status, "id": mission_id}))

def on_drone_location_discovery_request(data):
    is_connected = drone.connect()

    if is_connected:
        client.publish("drone-location-request-ack", json.dumps({"station_id": station_id, "mission_id": data['mission_id']}))


def continue_mission(data):
    log('continuing mission')

    dest_station_id = data['dest_station_id']

    is_connected = drone.connect()
    
    if is_connected:
        log('connected to drone - items loaded')
        
        # POST http://mcu/misson/generateplan (cur, dest)
        
        flightPlan = generate_flight_plan(station_id, dest_station_id)

        flightPlanUUID = upload_flight_plan(flightPlan)

        assert drone(
            Start(flightPlanUUID, 'flightPlan', _timeout=10000)
        ).wait().success()

        publish_status_event('heading_dest')

        log('disconnected from drone - items loaded')

        drone.disconnect()
    else:
        log('failed to connect to drone - items loaded')

        publish_status_event('failed')

def start_mission(data):
    log('starting mission')

    # global mission_id; mission_id = data['id']
    src_station_id = data['src_station_id']

    if src_station_id == station_id:
        log('already on the right station!')
        publish_status_event('awaiting_load')
        return

    is_connected = drone.connect()

    if is_connected:
        log('connected to drone - start mission')
        
        flightPlan = generate_flight_plan(station_id, src_station_id)

        flightPlanUUID = upload_flight_plan(flightPlan)

        assert drone(
            Start(flightPlanUUID, 'flightPlan', _timeout=10000)
        ).wait().success()

        publish_status_event('heading_source')

        log('disconnected from drone - start mission')
        drone.disconnect()
    else:
        # log('failed to connect to drone - start mission')

        publish_status_event('failed')
 
def ack_load():
    print('acked load')
    global package_loaded_flag
    package_loaded_flag = True

def ack_receive():
    print('acked receive')
    global package_received_flag
    package_received_flag = True

def on_message(client, userdata, message):
    print(message.topic)
    data = json.loads(message.payload.decode('utf-8'))
    if(message.topic == 'drone-location-discovery-request'):
        on_drone_location_discovery_request(data)
    elif(message.topic == 'mission-request'):
        start_mission(data)
    elif(message.topic == 'mission-continue'):
        continue_mission(data)
    elif (message.topic == 'package-load-ack'):
        ack_load()
    elif (message.topic == 'package-receive-ack'):
        ack_receive()
        
def on_message_handler(client, userdata, message):
    t = threading.Thread(target = on_message, args = (client, userdata, message))
    t.start()

client.on_message = on_message_handler

client.loop_forever()

# hostname = socket.gethostname()
# local_ip = socket.gethostbyname(hostname)
# print(local_ip)

def execute_movements(movements: List[Point]):
    for movement in movements:
        drone(
            moveBy(movement['y'], movement['x'], 0, 0) # moveBy: +/- forward/back, +/- right/left, +/- down/up
            >> FlyingStateChanged(state="hovering", _timeout=5)
        ).wait()

        time.sleep(2)

def execute_mission(req):
    drone(
        TakeOff()
        >> FlyingStateChanged(state="hovering", _timeout=10)
    ).wait()

    time.sleep(1)
    
    execute_movements(req['homeToSourceInstructions'])
    print ('reached source')
    
    drone(
        Landing()
        >> FlyingStateChanged(state="landed", _timeout=10)
    ).wait()
    
    publish_status_event('waiting_loading_confirmation')

    while(not package_loaded_flag):
        time.sleep(1)
        
    drone(
        TakeOff()
        >> FlyingStateChanged(state="hovering", _timeout=10)
    ).wait()

    time.sleep(1)
    
    execute_movements(req['sourceToDestInstructions'])
    print ('reached dest')
    
    drone(
        Landing()
        >> FlyingStateChanged(state="landed", _timeout=10)
    ).wait()
    
    publish_status_event('waiting_receiving_confirmation')
    
    while(not package_received_flag):
        time.sleep(1)
        
    drone(
        TakeOff()
        >> FlyingStateChanged(state="hovering", _timeout=10)
    ).wait()

    time.sleep(1)
        
    execute_movements(req['destToHomeInstructions'])
    print ('mission complete')
    
    drone(
        Landing()
        >> FlyingStateChanged(state="landed", _timeout=10)
    ).wait()
    
    publish_status_event('finished')
    
    global is_executing_mission
    is_executing_mission = False

# client.loop_forever()

# def flyTo(location: Location):
#     dist = 100
#     while(dist > 0.5):
#         global curX
#         global curY
#         dist = math.sqrt(math.pow(location.lat - curX, 2) + math.pow(location.lng - curY, 2))
#         dirX = (location.lat - curX) / dist
#         dirY = (location.lng - curY) / dist
#         curX += dirX * 1
#         curY += dirY * 1
#         print(f'CurX {curX}, CurY {curY}')
#         time.sleep(0.1)
        
# @app.post("/start_mission")
# async def start_mission(req: MissionStartRequest, background_tasks: BackgroundTasks):
#     global mission_id, is_executing_mission, package_loaded_flag, package_received_flag
    
#     if(is_executing_mission):
#         return json.dumps({"success": False})
    
#     mission_id = req.id
#     is_executing_mission = True
    
#     package_loaded_flag = False
#     package_received_flag = False
#     background_tasks.add_task(execute_mission, req)
        
#     publish_status_event('starting')
    
#     return json.dumps({"success": True})

# @app.post("/package_loaded")
# async def continue_mission():
#     global package_loaded_flag
#     package_loaded_flag = True
    
#     return 'Ok'

# @app.post("/package_received")
# async def continue_mission():
#     global package_received_flag
#     package_received_flag = True
    
#     return 'Ok'

class FlightListener(olympe.EventListener):

    @olympe.listen_event(MavlinkFilePlayingStateChanged())
    def onMavlinkFilePlayingStateChanged(self, event, scheduler):
        print(
            "flight plan state = {state}".format(
                **event.args
            )
        )

    @olympe.listen_event(FlyingStateChanged())
    def onFlyingStateChanged(self, event, scheduler):
        file_object = open('/app/log', 'a')
        # Append 'hello' at the end of file
        file_object.write('flying state changed')
        # Close the file
        file_object.close()
        
        # send update to MCU


if(__name__ == 'main'):
    # station_id = sys.argv[1]
    pass
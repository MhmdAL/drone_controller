import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged

from logging import exception
from typing import List, Dict
import time
import math
import threading
import requests
import json
import os
import socket
import sys
import paho.mqtt.client as mqtt

CONTROLLER_IP = "10.202.0.1"
drone = olympe.Drone(CONTROLLER_IP)
drone.connect()

class Point():
    x: float
    y: float

curX = 0
curY = 0

mission_id = 0
is_executing_mission = False

package_loaded_flag = False
package_received_flag = False

drone_id = os.environ.get('DRONE_ID')
print(f'drone id: {drone_id}')

def start_mission(data):
    print('starting mission')
    global mission_id, is_executing_mission, package_loaded_flag, package_received_flag
    
    mission_id = data['id']
    is_executing_mission = True
    
    package_loaded_flag = False
    package_received_flag = False
        
    publish_status_event('starting')
    
    drone(
        TakeOff()
        >> FlyingStateChanged(state="hovering", _timeout=10)
        >> moveBy(-1, -1, 0, 0)
        >> moveBy(1, 1, 0, 0)
        >> moveBy(-1, -1, 0, 0)
    ).wait()

    # execute_mission(data)

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
    if(message.topic == 'mission-request'):
        start_mission(data)
    elif (message.topic == 'package-load-ack'):
        ack_load()
    elif (message.topic == 'package-receive-ack'):
        ack_receive()
        
def on_message_handler(client, userdata, message):
    t = threading.Thread(target = on_message, args = (client, userdata, message))
    t.start()

client = mqtt.Client('drone')
client.connect('broker.emqx.io')
client.subscribe("mission-request")
client.subscribe("package-load-ack")
client.subscribe("package-receive-ack")
client.on_message = on_message_handler

# hostname = socket.gethostname()
# local_ip = socket.gethostbyname(hostname)
# print(local_ip)

def publish_status_event(status):
    client.publish("mission-status-update", json.dumps({"status": status, "id": mission_id}))

def execute_movements(movements: List[Point]):
    global curX, curY
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

client.loop_forever()

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

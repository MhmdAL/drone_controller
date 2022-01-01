from models import Location, Point, MissionStartRequest
from logging import exception
from fastapi import BackgroundTasks, FastAPI
from typing import List, Dict
import time
import math
import threading
import requests
import pika
import json
import os
import socket

app = FastAPI()

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')

drone_id = os.environ.get('DRONE_ID')
print(f'drone id: {drone_id}')

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(local_ip)

requests.put("http://localhost:3001/drone", json={
                "id": drone_id,
                "ip": local_ip,
})

curX = 0
curY = 0

mission_id = 0
is_executing_mission = False

class MyTask(threading.Thread):
    def run(self,*args,**kwargs):
        while True:
            # requests.put("http://localhost:3001/update_mission", json={
            #     "id": mission_id,
            #     "current_lat": curX,
            #     "current_lng": curY
            # })
            print(f'CurX {curX}, CurY {curY}')
            print('updating BE..')
            time.sleep(5)

t = MyTask()

package_loaded_flag = False
package_received_flag = False

def publish_status_event(status):
    channel.basic_publish(exchange='',
                      routing_key='mission-status-update-queue',
                      body=json.dumps({"status": status, "id": mission_id}))

def execute_movements(movements: List[Point]):
    global curX, curY
    for movement in movements:
        curX += movement.x
        curY += movement.y
        time.sleep(5)

def execute_mission(req: MissionStartRequest):
    execute_movements(req.homeToSourceInstructions)
    print ('reached source')
    
    publish_status_event('waiting_loading_confirmation')

    while(not package_loaded_flag):
        time.sleep(1)
        
    execute_movements(req.sourceToDestInstructions)
    print ('reached dest')
    
    publish_status_event('waiting_receiving_confirmation')
    
    while(not package_received_flag):
        time.sleep(1)
        
    execute_movements(req.destToHomeInstructions)
    print ('mission complete')
    
    publish_status_event('finished')
    
    global is_executing_mission
    is_executing_mission = False

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
        
@app.post("/start_mission")
async def start_mission(req: MissionStartRequest, background_tasks: BackgroundTasks):
    global mission_id, is_executing_mission, package_loaded_flag, package_received_flag
    
    if(is_executing_mission):
        return json.dumps({"success": False})
    
    mission_id = req.id
    is_executing_mission = True
    
    package_loaded_flag = False
    package_received_flag = False
    background_tasks.add_task(execute_mission, req)
        
    publish_status_event('starting')
    
    return json.dumps({"success": True})

@app.post("/package_loaded")
async def continue_mission():
    global package_loaded_flag
    package_loaded_flag = True
    
    return 'Ok'

@app.post("/package_received")
async def continue_mission():
    global package_received_flag
    package_received_flag = True
    
    return 'Ok'
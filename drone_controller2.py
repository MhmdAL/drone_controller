from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel
from typing import List, Dict
import time
import math
import threading
from pydantic.types import Json
import requests
from requests.api import request
import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')

class Location(BaseModel):
    lat: float
    lng: float

class Point(BaseModel):
    x: float
    y: float
    
class MissionStartRequest(BaseModel):
    id: int
    homeToSourceInstructions: List[Point]
    sourceToDestInstructions: List[Point]
    destToHomeInstructions: List[Point]

app = FastAPI()

curX = 0
curY = 0

mission_id = 0

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
                      body=json.dumps({"status": status}))

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
    global mission_id, package_loaded_flag, package_received_flag
    mission_id = req.id
    package_loaded_flag = False
    package_received_flag = False
    background_tasks.add_task(execute_mission, req)
    
    # t.start()
    
    publish_status_event('starting')
    
    return 'Ok'

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
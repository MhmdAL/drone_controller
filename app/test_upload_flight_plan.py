import olympe
import os
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, moveTo, Landing
from olympe.messages.ardrone3.PilotingState import moveToChanged, FlyingStateChanged, PositionChanged
from olympe.messages.ardrone3.PilotingEvent import moveByEnd
from olympe.messages.common.Mavlink import Start
import time
import requests
import os

DRONE_IP = os.environ.get("DRONE_IP", "192.168.42.1")

def test():
    drone = olympe.Drone(DRONE_IP)

    drone.connect()

    with open('/app/plan.txt', 'rb') as f:
        plan = f.read()

    res = requests.put(f'http://{DRONE_IP}/api/v1/upload/flightplan', data=plan, headers={'Content-Type': 'application/octet-stream'})

    drone.disconnect()
    
    print(res.content)

if __name__ == "__main__":
    test()
    
  
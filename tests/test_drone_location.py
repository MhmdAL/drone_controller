import olympe
import os
import time
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged
from olympe.messages.ardrone3.GPSSettingsState import HomeChanged

DRONE_IP = os.environ.get("DRONE_IP", "192.168.42.1")

def test():
    drone = olympe.Drone(DRONE_IP)
    drone.connect(timeout = 20)
    
    res = drone.get_state(HomeChanged)

    drone.disconnect()
    
    print('\n==============================\nLatitude:{}\nLongitude:{}\nAltitude:{}\n==============================\n'.format(res['latitude'], res['longitude'], res['altitude']))

if __name__ == "__main__":
    test()
import olympe
import os
import time
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged

DRONE_IP = os.environ.get("DRONE_IP", "192.168.42.1")

def test_physical_drone():
    drone = olympe.Drone(DRONE_IP)
    drone.connect(timeout = 20)
    
    assert drone(
        TakeOff(_timeout=15)
        >> FlyingStateChanged(state="hovering")
    ).wait().success()

    assert drone(
        Landing(_timeout=15)
    ).wait().success()

    drone.disconnect()




if __name__ == "__main__":
    test_physical_drone()
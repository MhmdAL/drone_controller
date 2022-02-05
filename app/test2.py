import olympe
import os
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, moveTo, Landing
from olympe.messages.ardrone3.PilotingState import moveToChanged, FlyingStateChanged
from olympe.messages.ardrone3.PilotingEvent import moveByEnd
from olympe.messages.common.Mavlink import Start

DRONE_IP = os.environ.get("DRONE_IP", "10.202.0.1")

def test_moveby2():
    drone = olympe.Drone(DRONE_IP)

    drone.connect()

    assert drone(
        Start("ab1cd1f9ae04bfbc0c469e2e9ee3fd4b", 'flightPlan', _timeout=10000)
    ).wait().success()

    drone.disconnect()



if __name__ == "__main__":
    test_moveby2()
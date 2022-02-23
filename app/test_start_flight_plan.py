import olympe
from olympe.messages.common.Mavlink import Start
import os
import sys

flightPlanUUID = str(sys.argv[1])

DRONE_IP = os.environ.get("DRONE_IP", "192.168.42.1")

drone = olympe.Drone(DRONE_IP)

drone.connect()

assert drone(
    Start(flightPlanUUID, 'flightPlan', _timeout=10000)
).wait().success()

drone.disconnect()
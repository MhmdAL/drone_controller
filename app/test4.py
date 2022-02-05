import olympe
import os
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, moveTo, Landing
from olympe.messages.ardrone3.PilotingState import moveToChanged, FlyingStateChanged, PositionChanged
from olympe.messages.ardrone3.PilotingEvent import moveByEnd
from olympe.messages.common.Mavlink import Start
import time
import requests
import os

DRONE_IP = os.environ.get("DRONE_IP", "10.202.0.1")

def print_event(event):
    # Here we're just serializing an event object and truncate the result if necessary
    # before printing it.
    if isinstance(event, olympe.ArsdkMessageEvent):
        max_args_size = 60
        args = str(event.args)
        args = (args[: max_args_size - 3] + "...") if len(args) > max_args_size else args
        file_object = open('/app/log', 'a')
        # Append 'hello' at the end of file
        file_object.write("{}({})\n".format(event.message.fullName, args))
        # Close the file
        file_object.close()
    else:
        print(str(event))

# This is the simplest event listener. It just exposes one
# method that matches every event message and prints it.
class EveryEventListener(olympe.EventListener):
    @olympe.listen_event(PositionChanged(_policy="wait"))
    def onPositionChanged(self, event, scheduler):
        print(
            "latitude = {latitude} longitude = {longitude} altitude = {altitude}".format(
                **event.args
            )
        )

        file_object = open('/app/log', 'a')

        file_object.write("latitude = {latitude} longitude = {longitude} altitude = {altitude}".format(
                **event.args
        ))
        
        file_object.close()

def test_moveby2():
    drone = olympe.Drone(DRONE_IP)
    listener = EveryEventListener(drone)
    listener.subscribe()

    drone.connect()

    with open('/app/plan.txt', 'rb') as f:
        plan = f.read()

    res = requests.put(f'http://{DRONE_IP}/api/v1/upload/flightplan', data=plan, headers={'Content-Type': 'application/octet-stream'})

    print(res.content)
    
    drone.disconnect()



if __name__ == "__main__":
    test_moveby2()
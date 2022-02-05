import olympe
import os
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, moveTo, Landing
from olympe.messages.ardrone3.PilotingState import moveToChanged, FlyingStateChanged
from olympe.messages.ardrone3.PilotingEvent import moveByEnd
from olympe.messages.common.Mavlink import Start
import time

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
    @olympe.listen_event(FlyingStateChanged(_policy="wait") | FlyingStateChanged(_policy="check") | FlyingStateChanged(_policy="check_wait") )
    def onAnyEvent(self, event, scheduler):
        print_event(event)

def test_moveby2():
    drone = olympe.Drone(DRONE_IP)
    listener = EveryEventListener(drone)
    listener.subscribe()
    drone.connect()

    time.sleep(100)

    drone.disconnect()



if __name__ == "__main__":
    test_moveby2()
# -*- coding: UTF-8 -*-

import re
import sys
import olympe
import time
import socket
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing, moveTo
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged, GpsLocationChanged
from olympe.messages.ardrone3.PilotingSettingsState import MaxTiltChanged

olympe.log.update_config({"loggers": {"olympe": {"level": "ERROR"}}})

DRONE_IP = "192.168.42.1"
CONTROLLER_IP = "192.168.53.1"


class DDSDrone:
    def takeoff():
        print("taking off")

def main():
    
    # coords[]
    # while(coords.any())
    #   await moveto(coords[i])
    #   coords.removeat(i)
    
    drone = olympe.Drone(CONTROLLER_IP)
    
    with FlightListener(drone):
        drone.connect()  

        # print(drone.get_state(GpsLocationChanged)["latitude"])

        s = socket.socket()        
        s.bind(('', int(str(sys.argv[1]))))
        s.listen(5)

        while True:

            c, addr = s.accept() 

            while True:
                x = c.recv(1024).decode()
        
                if (x == 'up'):
                    drone(
                        TakeOff()
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                    ).wait()

                    c.send('ok: drone hovering'.encode())
                elif (x == 'down'):
                    drone(
                        Landing()
                        >> FlyingStateChanged(state="landed", _timeout=10)
                    ).wait()




                    c.send('ok: drone landed'.encode())
                elif (x.startswith('move:')):
                    values = x.split(':')[1].split(',')

                    drone(
                        moveBy(float(values[0]), float(values[1]), float(values[2]), float (values[3])) # moveBy: +/- forward/back, +/- right/left, +/- down/up
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                    ).wait()

                    c.send('ok: done moving'.encode())
                elif (x.startswith('moveto:')):
                    values = x.split(':')[1].split(',')

                    drone(
                        moveTo(float(values[0]), float(values[1]), float(values[2]), 1, 0) # moveBy: +/- forward/back, +/- right/left, +/- down/up
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                    ).wait()

                    c.send('ok: done moving to location'.encode())
                elif (x == 'poc'):
                    drone(
                        TakeOff()
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> moveBy(15, 0, 0, 0)
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> moveBy(-10, 0, 0, 0)
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> Landing()
                        >> FlyingStateChanged(state="landed", _timeout=10)
                    ).wait()

                    c.send('ok: finished PoC'.encode())
                elif (x == 'poc2'):
                    drone(
                        TakeOff()
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> moveBy(5, 0, 0, 0)
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> moveBy(0, 5, 0, 0)
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> moveBy(-5, 0, 0, 0)
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> moveBy(0, -5, 0, 0)
                        >> FlyingStateChanged(state="hovering", _timeout=5)
                        >> Landing()
                        >> FlyingStateChanged(state="landed", _timeout=10)
                    ).wait()

                    c.send('ok: finished PoC'.encode())



if __name__ == "__main__":
    main()



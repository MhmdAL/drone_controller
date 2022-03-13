import sys
import utils
import mqtt_handler
import drone_controller
import schedule
import time
import threading
import station_state as State
import fingerprint_handler

def init():
    State.set_station_id(int(sys.argv[1]))

    utils.init_logger(State.station_id)
    drone_controller.init()
    
    scheduler_task = threading.Thread(target = run_schedule)
    scheduler_task.start()

    fingerprint_handler.init()
    
    mqtt_handler.init()
    mqtt_handler.start()

# Needed to run the schedule module
def run_schedule():
    while(True):
        schedule.run_pending()

if __name__== "__main__":
    init()

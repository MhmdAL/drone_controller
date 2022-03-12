import sys
import utils
import mqtt_handler
import drone_controller
import schedule
import time
import threading

station_id = None

def init():
    global station_id
    if len(sys.argv) > 1:
        station_id = sys.argv[1]
    else:
        station_id = 1

    utils.init_logger(station_id)
    drone_controller.init()
    
    scheduler_task = threading.Thread(target = run_schedule)
    scheduler_task.start()

    mqtt_handler.init()
    mqtt_handler.start()

# Needed to run the schedule module
def run_schedule():
    while(True):
        schedule.run_pending()

if __name__== "__main__":
    init()

import mqtt_handler as MQTT
import olympe
from olympe.messages.ardrone3.Piloting import TakeOff, moveBy, Landing
from olympe.messages.ardrone3.PilotingState import FlyingStateChanged, GpsLocationChanged
from olympe.messages.ardrone3.GPSSettingsState import HomeChanged
from olympe.messages.common.MavlinkState import MavlinkFilePlayingStateChanged
from olympe.messages.drone_manager import connection_state
from olympe.messages.common.Mavlink import Start
from olympe.messages.common.Common import AllStates
import requests
import json
import schedule
from utils import log, log_event
import os
import station_state as State
import fingerprint_handler as FP

olympe.log.update_config({"loggers": {"olympe": {"level": "INFO"}}})

DRONE_IP = os.environ.get("DRONE_IP", "192.168.42.1")
DRONE_ID = os.environ.get('DRONE_ID')

drone = olympe.Drone(DRONE_IP)

expected_fpid = None
expected_rfid = None
station_type = None

listener = None

def init():
    schedule.every(1).seconds.do(try_connect)

    MQTT.on_drone_location_request += on_drone_location_discovery_request
    MQTT.on_start_mission_request += start_mission
    MQTT.on_land_request += land
    MQTT.on_station_update_request += handle_station_assignment

    FP.on_finger_detected += on_finger_detected

def try_connect():
    if drone.connected:
        return True
    
    log ('retrying connection to drone..')

    global listener; 
    if listener != None:
        listener.unsubscribe()

    listener = FlightListener(drone)
    listener.subscribe()

    print('Connected? {}'.format(drone.connected))

    is_connected = drone.connect()
    if is_connected:
        print('connected')

    return is_connected

def get_drone_position():
    res = drone.get_state(HomeChanged)

    log('lat: {}, lng: {}, alt: {}'.format(res['latitude'], res['longitude'], res['altitude']))

    return (res['latitude'], res['longitude'], res['altitude'])

def on_finger_detected(finger_id):
    if finger_id >= expected_fpid and finger_id < expected_fpid + 5:
        print('correct fingerprint')
        MQTT.publish_message('acknowledge-recipient-event', json.dumps({"station_id": State.station_id}))
    else:
        print('incorrect fingerprint')

def upload_flight_plan(bytes):
    log('uploading flight plan')
    res = requests.put(f'http://{DRONE_IP}/api/v1/upload/flightplan', data=bytes, headers={'Content-Type': 'application/octet-stream'})

    return res.json()

def upload_flight_plan_and_start_mission(flight_plan):
    flightPlanUUID = upload_flight_plan(flight_plan)

    assert drone(
        Start(flightPlanUUID, 'flightPlan', _timeout=10000)
    ).wait().success()

def on_drone_location_discovery_request(data):
    log('drone location discovery request received')
    is_connected = try_connect()

    if is_connected:
        MQTT.publish_message("drone-location-request-ack-event", json.dumps({"station_id": State.station_id}))

def on_drone_landed():
    log('sending drone landing message')
    MQTT.publish_message("drone-landed-event", json.dumps({"station_id": State.station_id}))

def on_drone_reached_destination():
    log('sending flight mission completed message')
    MQTT.publish_message("flight-mission-completed-event", json.dumps({"station_id": State.station_id}))
    
def start_mission(data):
    log('[StartMission] - starting mission')

    flight_plan = data['planText'].encode('utf-8')

    is_connected = try_connect()

    if is_connected:  
        upload_flight_plan_and_start_mission(flight_plan)      
    else:
        log('[StartMission] - could not connect to drone')

def land(data):
    log('[Land] - landing')

    is_connected = try_connect()

    if is_connected:        
        assert drone(
            Landing(_timeout=100)
        ).wait().success()
    else:
        log('[Land] - could not connect to drone')

def handle_station_assignment(data):
    global expected_fpid; expected_fpid = data['expected_fpid']
    global expected_rfid; expected_rfid = data['expected_rfid']
    global station_type; station_type = data['station_type']

class FlightListener(olympe.EventListener):

    @olympe.listen_event(FlyingStateChanged(state = 'flying', _policy = 'wait') >> FlyingStateChanged(state = 'hovering', _policy = 'wait'))
    def onFlyingThenHovering(self, event, scheduler):
        log_event(event)

        on_drone_reached_destination()

    @olympe.listen_event(FlyingStateChanged(state = 'landing', _policy = 'wait') >> FlyingStateChanged(state = 'landed', _policy = 'wait'))
    def onLanded(self, event, scheduler):
        log_event(event)

        on_drone_landed()

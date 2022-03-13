from multiprocessing import Event
import serial
import adafruit_fingerprint
from Event import Event
import threading

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

on_finger_detected = Event()

def init():
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Fingerprint templates: ", finger.templates)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Number of templates found: ", finger.template_count)
    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to get system parameters")

    t = threading.Thread(target = run)
    t.start()

def run():
    while True:
        if get_fingerprint():
            on_finger_detected(finger.finger_id)

def get_fingerprint():
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

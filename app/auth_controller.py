import serial
import adafruit_fingerprint

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

print("----------------")
if finger.read_templates() != adafruit_fingerprint.OK:
    raise RuntimeError("Failed to read templates")
print("Fingerprint templates: ", finger.templates)
if finger.count_templates() != adafruit_fingerprint.OK:
    raise RuntimeError("Failed to read templates")
print("Number of templates found: ", finger.template_count)
if finger.read_sysparam() != adafruit_fingerprint.OK:
    raise RuntimeError("Failed to get system parameters")

def get_fingerprint():
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

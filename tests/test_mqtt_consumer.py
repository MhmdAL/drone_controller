import threading
import json
import paho.mqtt.client as mqtt

def on_message(client, userdata, message):
    data = json.loads(message.payload.decode('utf-8'))
    print(message.topic)
        
def on_message_handler(client, userdata, message):
    t = threading.Thread(target = on_message, args = (client, userdata, message))
    t.start()

client = mqtt.Client('drone_station')
client.connect('broker.emqx.io', 1883, 60)

client.subscribe('mission-request')
client.subscribe('drone-location-request')

client.on_message = on_message_handler

client.loop_forever()

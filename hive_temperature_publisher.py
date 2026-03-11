import paho.mqtt.client as mqtt
import ssl
import json
import time
import random

# --- HiveMQ Cloud Settings ---
# Found in your HiveMQ Cloud Console
MQTT_BROKER = "c6f88df75120418999bec7e5d6aed17a.s1.eu.hivemq.cloud" 
MQTT_PORT = 8883
MQTT_USER = "Psdtopicy"  # Your HiveMQ Cloud username
MQTT_PASSWORD = "Psdtopicygroup2"

# --- ThingsBoard Gateway Topic ---
# Using the gateway API allows you to specify the device name in the JSON
MQTT_TOPIC = "v1/gateway/telemetry"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Successfully connected to HiveMQ Cloud!")
    else:
        print(f"❌ Connection failed with code {rc}")

# 1. Initialize the Client
client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

# 2. Setup TLS (Required for HiveMQ Cloud)
client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

client.on_connect = on_connect

# 3. Connect
print(f"Connecting to {MQTT_BROKER}...")
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

try:
    while True:
        # Generate dummy data
        temp = round(random.uniform(20.0, 30.0), 2)
        
        # ThingsBoard Gateway format: {"DeviceName": [{"key": "value"}]}
        payload = {
        "Cloud-Simulator-01": {
            "temperature": temp,
            "status": "active"
    }
}
        
        # Publish
        result = client.publish(MQTT_TOPIC, json.dumps(payload), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"🚀 Sent: {temp}°C for 'Laptop-Sensor-01'")
        else:
            print("Failed to send message")
            
        time.sleep(5) # Send every 5 seconds

except KeyboardInterrupt:
    print("Stopping publisher...")
    client.disconnect()
    client.loop_stop()
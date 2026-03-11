import paho.mqtt.client as mqtt
import ssl
import os
import time

# Configuration
CLOUD_HOST = os.getenv("CLOUD_HOST")
CLOUD_USER = os.getenv("CLOUD_USER")
CLOUD_PASS = os.getenv("CLOUD_PASS")
INTERNAL_HOST = "tb-gateway" 

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud!")
        client.subscribe("#")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"Forwarding: {msg.topic} -> {msg.payload.decode()}")
    internal_client.publish(msg.topic, msg.payload)

# 1. Setup Internal Client
internal_client = mqtt.Client()
try:
    internal_client.connect(INTERNAL_HOST, 1883)
    internal_client.loop_start()
except Exception as e:
    print(f"⚠️ Internal connection failed: {e}. Is tb-gateway service running?")

# 2. Setup Cloud Client
cloud_client = mqtt.Client() # Default to Callback API v1 for 1.6.1
cloud_client.username_pw_set(CLOUD_USER, CLOUD_PASS)
cloud_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
cloud_client.on_connect = on_connect
cloud_client.on_message = on_message

print(f"Connecting to {CLOUD_HOST}...")
cloud_client.connect(CLOUD_HOST, 8883)
cloud_client.loop_forever()
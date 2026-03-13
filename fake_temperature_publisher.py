import argparse
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


DEFAULT_HOST = "34.61.243.83"
DEFAULT_PORT = 1883
DEFAULT_USERNAME = "guest"
DEFAULT_PASSWORD = "guest"
DEFAULT_TOPIC = "mqtt-broker-topic"


def build_client(host: str, port: int, username: str, password: str, use_tls: bool = False) -> mqtt.Client:
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.username_pw_set(username, password)
    if use_tls:
        client.tls_set()
    client.connect(host, port, keepalive=60)
    return client


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish fake temperature data to MQTT (HiveMQ Cloud ready).")
    parser.add_argument("--host", default=DEFAULT_HOST, help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="MQTT broker port (default: 1883)")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="MQTT username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="MQTT password")
    parser.add_argument("--tls", action="store_true", help="Enable TLS (for port 8883)")
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="MQTT topic")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between publishes")
    parser.add_argument("--count", type=int, default=0, help="Number of messages (0 = infinite)")
    parser.add_argument("--start-temp", type=float, default=24.5, help="Starting temperature in °C")
    args = parser.parse_args()

    client = build_client(args.host, args.port, args.username, args.password, args.tls)
    client.loop_start()

    temp_c = args.start_temp
    sent = 0

    try:
        while args.count == 0 or sent < args.count:
            temp_c += random.uniform(-0.25, 0.25)
            temp_c = round(max(15.0, min(40.0, temp_c)), 2)

            payload = {
                "device": "fake_sensor_01",
                "metric": "temperature",
                "value": temp_c,
                "unit": "C",
                "ts": datetime.now(timezone.utc).isoformat(),
            }

            result = client.publish(args.topic, json.dumps(payload), qos=1, retain=False)
            result.wait_for_publish()

            print(f"Published to {args.topic}: {payload}")
            sent += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

import time
import random
import json
from azure.iot.device import IoTHubDeviceClient, Message

#fake sensor anyways
CONNECTION_STRING = "HostName=iot-gateway-hub-psdtopicy.azure-devices.net;DeviceId=sensor-node-01;SharedAccessKey=T/ghyQpmXXPcrI9IHubKh5TUwpJxz61DjWVC7NbmJe0="

def main():
    print("Starting Azure IoT Hub Edge Gateway...")

    # Initialize the client using the secure connection string
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

    try:
        # Establish a secure TLS connection to Azure
        client.connect()
        print("Success! Connected securely to Azure IoT Hub.")

        while True:
            # Generate simulated edge telemetry
            temperature = round(random.uniform(22.0, 28.0), 2)
            humidity = round(random.uniform(40.0, 60.0), 2)

            payload = {
                "temperature": temperature,
                "humidity": humidity
            }

            # Package the payload as an Azure Message
            message = Message(json.dumps(payload))
            message.content_encoding = "utf-8"
            message.content_type = "application/json"

            # Publish to the cloud
            print(f"Publishing telemetry: {payload}")
            client.send_message(message)

            time.sleep(5) # Send every 5 seconds

    except KeyboardInterrupt:
        print("\nPublisher stopped by user.")
    finally:
        # Gracefully sever the connection
        client.disconnect()
        print("Disconnected from Azure IoT Hub.")

if __name__ == '__main__':
    main()
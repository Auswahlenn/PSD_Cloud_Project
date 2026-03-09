"""
Simple Telegram Alert Bot for IoT Sensors
- CO2 alert when > 800 ppm (easy to test by breathing)
- Panic button notification
- Water leak detection alert
"""

import os
import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import requests


# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1884'))

# MQTT Topics
TOPIC_CO2 = "milesight/uplink/24e124725d480213"  # AM103 sensor
TOPIC_BUTTON = "milesight/uplink/24e124535d381111"  # WS101 button
TOPIC_LEAK = "milesight/uplink/24e124993d354039"  # WS303 leak sensor
TOPIC_SWITCHES = "milesight/uplink/24e124756e041691"  # WS558 relay switches (8-channel)

# Thresholds
CO2_THRESHOLD = 800  # ppm - Easy to trigger for testing

# Track states to avoid duplicate alerts
last_button_msgid = None
leak_detected = False
last_co2_alert = 0

# Track WS558 switch states (1-8)
switch_states = {i: None for i in range(1, 9)}  # Switches 1-8
switch_initialized = False  # Track if we've received first uplink


def send_telegram_message(text):
    """Send a message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Sent to Telegram")
            return True
        else:
            print(f"❌ Failed to send: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC_CO2)
        client.subscribe(TOPIC_BUTTON)
        client.subscribe(TOPIC_LEAK)
        client.subscribe(TOPIC_SWITCHES)
        print(f"📡 Subscribed to: CO2, Panic Button, Leak Sensor, WS558 Switches")
    else:
        print(f"❌ Failed to connect. Return code: {rc}")


def on_message(client, userdata, msg):
    """Callback when a message is received"""
    global last_button_msgid, leak_detected, last_co2_alert, switch_states, switch_initialized
    
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Handle WS558 switch state changes from LoRaWAN uplink
        if msg.topic == TOPIC_SWITCHES:
            try:
                data = json.loads(msg.payload.decode())
                print(f"📩 Topic: {msg.topic}")
                print(f"   Data: {data}")
                
                # WS558 publishes switch states as: "switch_1": 1 or 0 (ON/OFF)
                for i in range(1, 9):
                    key = f"switch_{i}"
                    if key in data:
                        new_state = "ON" if data[key] == 1 else "OFF"
                        old_state = switch_states[i]
                        
                        # Update state
                        switch_states[i] = new_state
                        
                        # Send alert only if:
                        # 1. We've already initialized (received first uplink)
                        # 2. The state has actually changed
                        if switch_initialized and old_state is not None and old_state != new_state:
                            emoji = "🟢" if new_state == "ON" else "⚫"
                            message = f"{emoji} <b>Switch {i} turned {new_state}</b>\n\n"
                            message += f"Switch: Lab Switch {i}\n"
                            message += f"Status: <b>{new_state}</b>\n"
                            message += f"Time: {timestamp}"
                            send_telegram_message(message)
                            print(f"   ✅ Switch {i} alert sent!")
                
                # Mark as initialized after first uplink
                if not switch_initialized:
                    switch_initialized = True
                    print(f"   ℹ️ Switch states initialized: {switch_states}")
                    
            except json.JSONDecodeError:
                print(f"⚠️ Invalid JSON from {msg.topic}: {msg.payload}")
            except Exception as e:
                print(f"❌ Error processing WS558 message: {e}")
            return
        
        # Parse JSON payload for other sensor data
        data = json.loads(msg.payload.decode())
        
        print(f"📩 Topic: {msg.topic}")
        print(f"   Data: {data}")
        
        # 1. CO2 Alert (with 60 second cooldown to avoid spam)
        if msg.topic == TOPIC_CO2 and 'co2' in data:
            co2_value = float(data['co2'])
            current_time = time.time()
            
            if co2_value > CO2_THRESHOLD and (current_time - last_co2_alert) > 60:
                message = f"🚨 <b>HIGH CO2 ALERT!</b>\n\n"
                message += f"Level: <b>{co2_value:.0f} ppm</b>\n"
                message += f"Threshold: {CO2_THRESHOLD} ppm\n"
                message += f"Time: {timestamp}"
                send_telegram_message(message)
                last_co2_alert = current_time
        
        # 2. Panic Button Press
        elif msg.topic == TOPIC_BUTTON and 'button' in data:
            button_value = data['button']
            
            # Get the message ID to avoid duplicates
            msgid = data.get('button_single_msgid') or data.get('button_double_msgid')
            
            # Only process if this is a new button press (different msgid)
            if msgid and msgid != last_button_msgid:
                if button_value == 1:
                    # Single press
                    message = f"🚨 <b>PANIC BUTTON PRESSED!</b>\n\n"
                    message += f"⚠️ Emergency alert activated\n"
                    message += f"Type: Single Press\n"
                    message += f"Time: {timestamp}"
                    send_telegram_message(message)
                    last_button_msgid = msgid
                    print(f"   ✅ Single press detected!")
                    
                elif button_value == 3:
                    # Double press
                    message = f"🚨🚨 <b>PANIC BUTTON DOUBLE-PRESSED!</b>\n\n"
                    message += f"⚠️⚠️ URGENT Emergency alert!\n"
                    message += f"Type: Double Press\n"
                    message += f"Time: {timestamp}"
                    send_telegram_message(message)
                    last_button_msgid = msgid
                    print(f"   ✅ Double press detected!")
            else:
                print(f"   ⏭️ Skipped (duplicate msgid)")
        
        # 3. Water Leak Detection
        elif msg.topic == TOPIC_LEAK and 'leak' in data:
            leak_status = int(data['leak'])
            
            if leak_status == 1 and not leak_detected:
                # Leak detected
                message = f"💧 <b>WATER LEAK DETECTED!</b>\n\n"
                message += f"Location: Lab\n"
                message += f"Status: <b>LEAK ACTIVE</b>\n"
                message += f"Time: {timestamp}"
                send_telegram_message(message)
                leak_detected = True
                
            elif leak_status == 0 and leak_detected:
                # Leak cleared
                message = f"✅ <b>Water Leak Cleared</b>\n\n"
                message += f"Location: Lab\n"
                message += f"Status: Normal\n"
                message += f"Time: {timestamp}"
                send_telegram_message(message)
                leak_detected = False
        
    except json.JSONDecodeError:
        print(f"⚠️ Invalid JSON: {msg.payload}")
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    
    # Validate configuration
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
        print("\nExample .env file:")
        print("TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        print("TELEGRAM_CHAT_ID=987654321")
        print("MQTT_BROKER=localhost")
        print("MQTT_PORT=1884")
        return
    
    print("🚀 Starting Telegram Alert Bot...")
    print(f"📡 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"🎯 CO2 Threshold: {CO2_THRESHOLD} ppm (blow into sensor to test!)")
    
    # Send startup message
    startup_msg = f"🤖 <b>Alert Bot Started</b>\n\n"
    startup_msg += f"✅ Monitoring CO2 (>{CO2_THRESHOLD} ppm)\n"
    startup_msg += f"✅ Monitoring Panic Button\n"
    startup_msg += f"✅ Monitoring Water Leak\n"
    startup_msg += f"✅ Monitoring WS558 Switches (1-8)\n"
    startup_msg += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_telegram_message(startup_msg)
    
    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect and start
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print("✅ Bot is running. Press Ctrl+C to stop.\n")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        send_telegram_message("🛑 <b>Alert Bot Stopped</b>")
        client.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
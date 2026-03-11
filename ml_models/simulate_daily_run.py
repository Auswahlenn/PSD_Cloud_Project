import os
import pandas as pd
import numpy as np

from datetime import datetime
import json
import time
import paho.mqtt.client as mqtt
from lstm_model import UnivariateLSTM
from utils import generate_fake_sensor_data, append_fake_data

# Configuration
DATA_FILE = 'sensor_history.csv'
MODEL_PATH = 'lstm_sensor_model'
DAYS_INITIAL_HISTORY = 60
LOOK_BACK = 24
FORECAST_DAYS = 1
USE_REAL_DATA = False # Set to True to use data from Postgres DB
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "ai/forecast/temperature"

def publish_to_mqtt(prediction):
    try:
        client = mqtt.Client()
        client.username_pw_set("thingsboard", "SecureServer123!")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        payload = {
            "timestamp": datetime.now().isoformat(),
            "temperature_prediction": float(prediction),
            "unit": "°C",
            "model": "LSTM_Univariate"
        }
        
        client.publish(MQTT_TOPIC, json.dumps(payload))
        client.disconnect()
        print(f"Published to MQTT: {payload}")
    except Exception as e:
        print(f"Failed to publish to MQTT: {e}")

def run_daily_task():
    print("=== Starting Daily AI/ML Task ===")
    
    # 1. Load or Initialize Data
    df = None
    
    if USE_REAL_DATA:
        print("Fetching REAL data from Database...")
        try:
            # Import Django setup to use models outside manage.py context
            import sys
            import django
            
            # Add project root to path
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'psd_V2.settings')
            django.setup()
            
            from ml_models.data_preparation import SensorDataPreparation
            df = SensorDataPreparation.extract_sensor_features(hours_back=DAYS_INITIAL_HISTORY*24)
            
            if df.empty:
                print("No real data found in DB. Falling back to synthetic data.")
                df = None
            else:
                # Map columns to match what `utils.py` produced? 
                # utils.py produced 'timestamp', 'value'
                # extract_sensor_features produces 'temperature', 'humidity', 'timestamp', etc.
                # We will just use temperature for this demo
                df = df[['timestamp', 'temperature']].rename(columns={'temperature': 'value'})
                print(f"Retrieved {len(df)} real records.")
                
        except Exception as e:
            print(f"Error fetching DB data: {e}")
            print("Ensure you run this with 'python manage.py shell' or setup django environment.")

    # Fallback/Default to CSV/Fake
    if df is None:
        if os.path.exists(DATA_FILE):
             print(f"Loading existing synthetic data from {DATA_FILE}...")
             df = pd.read_csv(DATA_FILE)
             df['timestamp'] = pd.to_datetime(df['timestamp'])
             
             if not USE_REAL_DATA:
                print("Simulating collection of new sensor data...")
                df = append_fake_data(df, hours=24, noise_level=0.8)
        else:
             print("Initializing with synthetic history...")
             df = generate_fake_sensor_data(days=DAYS_INITIAL_HISTORY, noise_level=0.8)
    
    if not USE_REAL_DATA:
        # Save updated synthetic data
        df.to_csv(DATA_FILE, index=False)

    
    # 2. Initialize Model
    lstm = UnivariateLSTM(look_back=LOOK_BACK)
    
    # Try to load existing model to continue training (Online/Incremental Learning concept)
    # Note: Keras models can be retrained.
    model_file_exists = os.path.exists(MODEL_PATH + '.keras')
    if model_file_exists:
        print("Loading existing model for retraining...")
        try:
            lstm.load(MODEL_PATH)
        except Exception as e:
            print(f"Could not load model: {e}. Starting fresh.")
    else:
        print("Initializing new LSTM model...")
    
    # 3. Retrain (Daily Update)
    # We train on the entire history or a sliding window of it. 
    # For this demo, we train on the last 30 days to keep it fast while maintaining recent trends.
    # 30 days * 24 hours = 720 points
    training_window_hours = 30 * 24
    if len(df) > training_window_hours:
        train_data = df['value'].values[-training_window_hours:]
    else:
        train_data = df['value'].values
        
    print(f"Retraining model on last {len(train_data)} data points...")
    lstm.train(train_data, epochs=10, batch_size=32)
    
    # 4. Save Updated Model
    lstm.save(MODEL_PATH)
    print("Model updated and saved.")
    
    # 5. Generate Forecast (Prediction)
    print("\ngenerating forecast for tomorrow...")
    predictions = lstm.predict_next_days(train_data, days_to_predict=FORECAST_DAYS)
    
    print(f"\nPredicted Temperature for next 24 hours (first 5):")
    for i, p in enumerate(predictions[:5]):
        print(f"Hour +{i+1}: {p:.2f}°C")
        
    print(f"\nAverage predicted temp: {np.mean(predictions):.2f}°C")
    
    # 6. Publish to MQTT
    # We'll publish the first prediction as the "current forecast"
    if predictions:
        publish_to_mqtt(predictions[0])

    print("=== Task Complete ===")

if __name__ == "__main__":
    # Ensure we are in the right directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("Starting AI/ML Service...")
    while True:
        try:
            run_daily_task()
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        # internal = 60 seconds (demo mode)
        print("Sleeping for 60 seconds...")
        time.sleep(60)

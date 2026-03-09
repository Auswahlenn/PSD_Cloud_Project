import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.db.models import Avg, Max, Min
import os

class SensorDataPreparation:
    """Prepare IoT sensor data for time-series ML prediction"""
    
    @staticmethod
    def extract_sensor_features(device_id=None, hours_back=168):
        """
        Extract sensor readings for time-series analysis
        
        Args:
            device_id: Specific device ID or None for all devices
            hours_back: Number of hours of historical data (default: 1 week)
        """
        from iot_devices.models import Device, SensorReading
        
        # Get sensor readings
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        readings = SensorReading.objects.filter(
            timestamp__gte=cutoff_time
        ).select_related('device')
        
        if device_id:
            readings = readings.filter(device_id=device_id)
        
        readings = readings.order_by('timestamp')
        
        data = []
        for reading in readings:
            features = {
                'device_id': reading.device.id,
                'device_name': reading.device.name,
                'device_type': reading.device.device_type,
                'timestamp': reading.timestamp,
                'temperature': reading.temperature,
                'humidity': reading.humidity,
                'pressure': getattr(reading, 'pressure', None),
                'light_level': getattr(reading, 'light_level', None),
                'motion_detected': getattr(reading, 'motion_detected', None),
                'hour': reading.timestamp.hour,
                'day_of_week': reading.timestamp.weekday(),
                'day_of_month': reading.timestamp.day,
                'month': reading.timestamp.month,
            }
            data.append(features)
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Create time-based features
            df = SensorDataPreparation._create_time_features(df)
            # Create lag features
            df = SensorDataPreparation._create_lag_features(df)
        
        return df
    
    @staticmethod
    def _create_time_features(df):
        """Create time-based features for better prediction"""
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['time_of_day'] = df['hour'].apply(
                lambda x: 'night' if x < 6 else 'morning' if x < 12 else 'afternoon' if x < 18 else 'evening'
            )
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['season'] = df['month'].apply(
                lambda x: 'winter' if x in [12, 1, 2] else 'spring' if x in [3, 4, 5] 
                else 'summer' if x in [6, 7, 8] else 'fall'
            )
        return df
    
    @staticmethod
    def _create_lag_features(df, target_cols=['temperature', 'humidity']):
        """Create lag features for time-series prediction"""
        for col in target_cols:
            if col in df.columns:
                # Last 1, 3, 6, 12, 24 hours
                for lag in [1, 3, 6, 12, 24]:
                    df[f'{col}_lag_{lag}h'] = df.groupby('device_id')[col].shift(lag)
                
                # Rolling statistics
                df[f'{col}_rolling_mean_6h'] = df.groupby('device_id')[col].rolling(window=6, min_periods=1).mean().reset_index(0, drop=True)
                df[f'{col}_rolling_std_6h'] = df.groupby('device_id')[col].rolling(window=6, min_periods=1).std().reset_index(0, drop=True)
                df[f'{col}_rolling_mean_24h'] = df.groupby('device_id')[col].rolling(window=24, min_periods=1).mean().reset_index(0, drop=True)
        
        return df
    
    @staticmethod
    def prepare_sequences(df, seq_length=24, forecast_horizon=6):
        """
        Prepare sequences for LSTM/time-series models
        
        Args:
            df: DataFrame with sensor data
            seq_length: Number of past hours to use
            forecast_horizon: Number of hours to predict ahead
        """
        sequences = []
        targets = []
        
        for device_id in df['device_id'].unique():
            device_data = df[df['device_id'] == device_id].sort_values('timestamp')
            
            temp_values = device_data['temperature'].values
            humidity_values = device_data['humidity'].values
            
            for i in range(len(device_data) - seq_length - forecast_horizon):
                # Input sequence
                seq = np.column_stack([
                    temp_values[i:i+seq_length],
                    humidity_values[i:i+seq_length]
                ])
                sequences.append(seq)
                
                # Target values (future predictions)
                target = np.column_stack([
                    temp_values[i+seq_length:i+seq_length+forecast_horizon],
                    humidity_values[i+seq_length:i+seq_length+forecast_horizon]
                ])
                targets.append(target)
        
        return np.array(sequences), np.array(targets)
    
    @staticmethod
    def export_to_csv(filename='sensor_training_data.csv', device_id=None):
        """Export prepared sensor data to CSV for Google Colab"""
        df = SensorDataPreparation.extract_sensor_features(device_id=device_id)
        
        # Drop rows with too many NaN values from lag features
        df = df.dropna(thresh=len(df.columns) * 0.7)
        
        df.to_csv(filename, index=False)
        print(f"Exported {len(df)} records to {filename}")
        return filename
    
    @staticmethod
    def get_device_statistics():
        """Get statistics for all devices"""
        from iot_devices.models import Device, SensorReading
        
        devices = Device.objects.all()
        stats = []
        
        for device in devices:
            readings = SensorReading.objects.filter(device=device)
            if readings.exists():
                device_stats = {
                    'device_id': device.id,
                    'device_name': device.name,
                    'total_readings': readings.count(),
                    'avg_temperature': readings.aggregate(Avg('temperature'))['temperature__avg'],
                    'max_temperature': readings.aggregate(Max('temperature'))['temperature__max'],
                    'min_temperature': readings.aggregate(Min('temperature'))['temperature__min'],
                    'avg_humidity': readings.aggregate(Avg('humidity'))['humidity__avg'],
                    'max_humidity': readings.aggregate(Max('humidity'))['humidity__max'],
                    'min_humidity': readings.aggregate(Min('humidity'))['humidity__min'],
                }
                stats.append(device_stats)
        
        return pd.DataFrame(stats)

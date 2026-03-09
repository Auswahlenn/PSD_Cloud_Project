import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_fake_sensor_data(days=30, start_date=None, noise_level=0.5):
    """
    Generates fake sensor data (e.g., Temperature) with a daily seasonality.
    
    Args:
        days (int): Number of days of data to generate.
        start_date (datetime): The starting timestamp. Defaults to now - days.
        noise_level (float): Magnitude of random noise to add.
        
    Returns:
        pd.DataFrame: DataFrame with 'timestamp' and 'value' columns.
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
        
    # Generate hourly data
    hours = days * 24
    timestamps = [start_date + timedelta(hours=i) for i in range(hours)]
    
    # Simulate Temperature:
    # - Base value: 25 degrees
    # - Daily cycle: sin wave with period 24 hours (amplitude 5)
    # - Random noise
    values = []
    for i in range(hours):
        # Time of day effect (sin wave)
        # i % 24 maps 0-23. 
        # sin(0) is mid, sin(pi/2) is peak. 
        # We want peak around 2 PM (14:00). 
        # (i - 14) shift? 
        # standard sin goes 0->1->0->-1.
        
        daily_pattern = 5 * np.sin((i / 24) * 2 * np.pi) 
        base_temp = 25
        noise = np.random.normal(0, noise_level)
        
        val = base_temp + daily_pattern + noise
        values.append(val)
        
    df = pd.DataFrame({
        'timestamp': timestamps,
        'value': values
    })
    
    return df

def append_fake_data(existing_df, hours=24, noise_level=0.5):
    """
    Appends new fake data to the end of an existing DataFrame.
    """
    last_timestamp = pd.to_datetime(existing_df['timestamp'].iloc[-1])
    start_date = last_timestamp + timedelta(hours=1)
    
    new_data = generate_fake_sensor_data(days=hours/24, start_date=start_date, noise_level=noise_level)
    
    # Return concatenated dataframe
    return pd.concat([existing_df, new_data], ignore_index=True)

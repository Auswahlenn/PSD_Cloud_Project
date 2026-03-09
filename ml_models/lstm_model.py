import numpy as np
import pandas as pd
import pickle
import os
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.models import load_model

class UnivariateLSTM:
    """
    A Univariate Time Series LSTM Model for generic sensor data forecasting.
    
    Theory:
    - Univariate: The model looks at the history of a single variable (e.g., Temperature) 
      to predict its future values. It does not use other features.
    - LSTM (Long Short-Term Memory): A type of Recurrent Neural Network (RNN) capable of 
      learning order dependence in sequence prediction problems.
      
    Process:
    1. Preprocessing: Scale data to [0, 1] for neural network stability.
    2. Windowing: Convert linear time series into a supervised learning problem.
       Input (X): [t-N, ..., t-1] -> Output (y): [t]
    3. Training: Learn the patterns.
    4. Forecasting: Use the last known window to predict the next step, then append the prediction 
       to the window to predict the step after that (recursive forecasting).
    """
    
    def __init__(self, look_back=60, forecast_horizon=1):
        """
        Args:
            look_back (int): The number of previous time steps to use as input variables. 
                             (e.g., 60 hours of history to predict the next hour).
            forecast_horizon (int): Number of steps to predict into the future (usually 1 for recursive).
        """
        self.look_back = look_back
        self.forecast_horizon = forecast_horizon
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
    def create_dataset(self, dataset):
        """
        Converts an array of values into a dataset matrix (X, Y).
        
        Args:
            dataset: numpy array of the time series values.
            
        Returns:
            np.array, np.array: X (inputs), Y (labels)
        """
        dataX, dataY = [], []
        # Loop through the dataset up to len - look_back - 1
        for i in range(len(dataset) - self.look_back - 1):
            a = dataset[i:(i + self.look_back), 0]
            dataX.append(a)
            dataY.append(dataset[i + self.look_back, 0])
            
        return np.array(dataX), np.array(dataY)

    def data_preprocessing(self, raw_data):
        """
        Scales the data and reshapes it for LSTM [samples, time steps, features].
        """
        # Ensure data is 2D array [samples, features]
        if isinstance(raw_data, list):
            raw_data = np.array(raw_data).reshape(-1, 1)
        elif isinstance(raw_data, pd.Series):
            raw_data = raw_data.values.reshape(-1, 1)
        elif isinstance(raw_data, np.ndarray) and raw_data.ndim == 1:
            raw_data = raw_data.reshape(-1, 1)

        # Fit and transform the data
        scaled_data = self.scaler.fit_transform(raw_data)
        return scaled_data

    def build_model(self):
        """
        Builds the LSTM model architecture.
        """
        self.model = Sequential()
        # LSTM Layer
        # units=50: Dimensionality of the output space.
        # return_sequences=False: We only need the output of the last time step.
        # input_shape: (time_steps, features). Features is 1 for univariate.
        self.model.add(LSTM(50, return_sequences=False, input_shape=(self.look_back, 1)))
        
        # Dense Layer
        # The output layer for the prediction (single value).
        self.model.add(Dense(1))
        
        # Compilation
        # optimizer='adam': Efficient stochastic gradient descent.
        # loss='mean_squared_error': Standard loss for regression problems.
        self.model.compile(optimizer='adam', loss='mean_squared_error')

    def train(self, data, epochs=20, batch_size=32):
        """
        Main method to train the model.
        
        Args:
            data (list/array/series): The complete history of the sensor data.
            epochs (int): Number of times to iterate over the entire dataset.
            batch_size (int): Number of samples per gradient update.
        """
        # 1. Preprocess
        scaled_data = self.data_preprocessing(data)
        
        # 2. Create X, Y
        X, y = self.create_dataset(scaled_data)
        
        # Reshape input to be [samples, time steps, features]
        # X starts as [samples, look_back]. Needs to be [samples, look_back, 1]
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))
        
        # 3. Build Model (if not already built)
        if self.model is None:
            self.build_model()
            
        # 4. Fit
        print(f"Training LSTM model with {len(X)} samples for {epochs} epochs...")
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=1)
        print("Training complete.")

    def predict_next_days(self, recent_data, days_to_predict=1):
        """
        Predict future values using the trained model.
        
        Args:
            recent_data: The most recent data points (must be at least 'look_back' length).
            days_to_predict: Number of days to forecast (assuming hourly data -> 24 * days).
            
        Returns:
            list: Predicted values in original scale.
        """
        if self.model is None:
            raise Exception("Model has not been trained yet!")
            
        # Number of hours to predict
        steps = days_to_predict * 24
        
        # Prepare initial input
        # Take the last 'look_back' points
        if len(recent_data) < self.look_back:
            raise ValueError(f"Not enough data to predict. Need {self.look_back} points.")
            
        current_batch = np.array(recent_data[-self.look_back:]).reshape(-1, 1)
        current_batch = self.scaler.transform(current_batch) # Scale using the fitted scaler
        
        # Reshape for LSTM [1, look_back, 1]
        current_input = current_batch.reshape(1, self.look_back, 1)
        
        predictions_scaled = []
        
        for _ in range(steps):
            # Predict the next step
            # pred is [[value]]
            pred = self.model.predict(current_input, verbose=0)
            
            # Store prediction
            predictions_scaled.append(pred[0, 0])
            
            # Update input batch: remove first, add new prediction
            # current_input has shape (1, 60, 1)
            # We want to shift everything left and put pred at the end
            
            # Remove first element from sequence
            new_seq = current_input[0, 1:, 0] # Shape (59,)
            # Append new prediction
            new_seq = np.append(new_seq, pred[0, 0]) # Shape (60,)
            # Reshape back to (1, 60, 1)
            current_input = new_seq.reshape(1, self.look_back, 1)
            
        # Inverse transform predictions to get real values
        predictions_scaled = np.array(predictions_scaled).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions_scaled)
        
        return predictions.flatten().tolist()

    def save(self, filepath):
        """Saves the model and scaler."""
        # Save Keras model
        model_file = filepath + '.keras'
        self.model.save(model_file)
        
        # Save scaler and attributes
        meta_data = {
            'scaler': self.scaler,
            'look_back': self.look_back
        }
        with open(filepath + '_meta.pkl', 'wb') as f:
            pickle.dump(meta_data, f)
        print(f"Model saved to {model_file}")

    def load(self, filepath):
        """Loads a saved model."""
        model_file = filepath + '.keras'
        if not os.path.exists(model_file):
             # Try legacy .h5 or just path
            if os.path.exists(filepath):
                 model_file = filepath
            else:
                 raise FileNotFoundError(f"No model found at {model_file}")
                 
        self.model = load_model(model_file)
        
        with open(filepath + '_meta.pkl', 'rb') as f:
            meta_data = pickle.load(f)
            self.scaler = meta_data['scaler']
            self.look_back = meta_data['look_back']
        print(f"Model loaded from {filepath}")

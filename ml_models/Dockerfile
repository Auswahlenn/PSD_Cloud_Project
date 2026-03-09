FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Using tensorflow-cpu to reduce image size if only inference/training small models
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scikit-learn \
    tensorflow-cpu \
    paho-mqtt

COPY . .

CMD ["python", "simulate_daily_run.py"]

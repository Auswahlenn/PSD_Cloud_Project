FROM python:3.10-slim

WORKDIR /app

# Install required libraries
RUN pip install python-telegram-bot paho-mqtt requests

# Copy the bot scripts
COPY . /app/

# Run the bot
CMD ["python", "alert_bot.py"]
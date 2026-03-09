# Use the official Playwright image that already has all system dependencies installed
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements file first
COPY requirements.txt .

# Install your Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot's code into the container
COPY . .

# Expose the port for your Flask server (for UptimeRobot)
EXPOSE 8080

# Command to run your bot
CMD ["python", "bot.py"]

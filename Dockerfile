# Use a standard, lightweight Python image
FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install your Python packages (including the latest Playwright)
RUN pip install --no-cache-dir -r requirements.txt

# Download the exact browser version that matches your installed Python package
RUN playwright install chromium

# Install the necessary system dependencies (this works here because Docker builds as root)
RUN playwright install-deps

# Copy your bot code
COPY . .

# Start the bot
CMD ["python", "bot.py"]

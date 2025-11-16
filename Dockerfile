# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Update and install system dependencies (including ffmpeg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container
COPY src/ ./src

# Create the download directory and set appropriate permissions
RUN mkdir -p /tmp/downloads && chown -R www-data:www-data /tmp/downloads

# Expose the port the app runs on
EXPOSE 8080

# Define the command to run the application using Gunicorn
# The app object is now located in src.web.app
CMD ["gunicorn", "src.web.app:app", "--bind", "0.0.0.0:8080", "--timeout", "120", "--user", "www-data", "--group", "www-data"]

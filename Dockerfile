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

# --- Configuration via Environment Variables ---

# To use a proxy, set this environment variable at runtime.
# Example: -e PROXY_URL="http://user:pass@host:port"
ENV PROXY_URL=""

# To use a cookies file, you can build it into the image or mount it as a volume.
# 1. To build it in: place your cookies.txt in the root and build with --build-arg COOKIES_FILE=cookies.txt
# 2. To mount it: run with -v /path/to/local/cookies.txt:/app/cookies.txt -e COOKIES_FILE_PATH=/app/cookies.txt
ARG COOKIES_FILE
COPY ${COOKIES_FILE:-/dev/null} /app/cookies.txt
ENV COOKIES_FILE_PATH=/app/cookies.txt

# Set a default download directory
ENV DOWNLOAD_DIR=/tmp/downloads

# Create the download directory and set appropriate permissions
# Note: The user www-data needs to own the directory to write files.
RUN mkdir -p ${DOWNLOAD_DIR} && chown -R www-data:www-data ${DOWNLOAD_DIR}

# Expose the port the app runs on
EXPOSE 8080

# Define the command to run the application using Gunicorn
# Running as www-data user for better security.
CMD ["gunicorn", "src.web.app:app", "--bind", "0.0.0.0:8080", "--timeout", "120", "--user", "www-data", "--group", "www-data"]

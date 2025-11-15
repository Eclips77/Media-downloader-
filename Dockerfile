# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory in the container
WORKDIR /app

# 3. Update and install system dependencies (ffmpeg)
# Run as root and clean up apt-get lists to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 4. Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code into the container
COPY . .

# 6. Expose the port the app runs on. Render will automatically use this.
EXPOSE 8080

# 7. Define the command to run the application
# We bind to 0.0.0.0 to allow external connections to the container.
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]
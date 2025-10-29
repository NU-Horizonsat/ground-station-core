# Ground Station Core Docker Image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libusb-1.0-0-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Note: Some packages may fail without system SDR libraries installed
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Some packages failed to install (likely SDR-related), continuing..." && \
     pip install --no-cache-dir numpy scipy matplotlib requests fastapi uvicorn pydantic python-multipart pyyaml python-dotenv influxdb-client pyserial skyfield python-dateutil aiofiles websockets)

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/results /app/data /app/config

# Expose API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GSC_CONFIG_DIR=/app/config

# Run the API server
CMD ["python", "backend/api_server.py"]

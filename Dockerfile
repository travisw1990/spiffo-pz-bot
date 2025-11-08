# Spiffo Discord Bot - Production Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai/ ./ai/
COPY analytics/ ./analytics/
COPY bot/ ./bot/
COPY knowledge/ ./knowledge/
COPY server/ ./server/
COPY utils/ ./utils/
COPY main.py .

# Create directories for runtime data
RUN mkdir -p /app/knowledge_base /app/logs

# Run the bot
CMD ["python", "-u", "main.py"]

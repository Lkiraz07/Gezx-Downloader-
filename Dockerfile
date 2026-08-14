FROM python:3.11-slim

# Install system dependencies (ffmpeg and git are required for yt-dlp & metadata)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose default port for Render web service health check
EXPOSE 8080

# Run the application entry point
CMD ["python", "bot.py"]

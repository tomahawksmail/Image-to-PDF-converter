FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies (for Pillow)
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 5613

# Run with production server
CMD ["gunicorn", "-b", "0.0.0.0:5613", "main:app"]
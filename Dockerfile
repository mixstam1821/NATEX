# ==============================
# NATEX Dockerfile
# ==============================

# 1. Use official Python base image
FROM python:3.11-slim

# 2. Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# 3. Install system dependencies
# Needed for cartopy, shapely, pillow, pyproj, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libproj-dev \
    proj-data \
    proj-bin \
    libgeos-dev \
    libgdal-dev \
    gdal-bin \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    libatlas-base-dev \
    liblapack-dev \
    libopenblas-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# 4. Create app directory
WORKDIR /app

# 5. Copy requirements.txt
COPY requirements.txt .

# 6. Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# 7. Copy project files
COPY . .

# 8. Expose Bokeh server port
EXPOSE 5006

# 9. Default command to run Bokeh app
CMD ["bokeh", "serve", "--allow-websocket-origin=*", "--port", "5006", "--address", "0.0.0.0", "."]

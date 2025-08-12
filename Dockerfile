# ==============================
# NATEX Dockerfile
# ==============================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System deps for cartopy/shapely/pyproj/Pillow/GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libproj-dev proj-data proj-bin \
    libgeos-dev \
    libgdal-dev gdal-bin \
    libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev \
    libatlas-base-dev liblapack-dev libopenblas-dev \
    git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# App code
COPY . .

# Match the port you actually serve on
EXPOSE 5098

# IMPORTANT: remove the trailing dot!
# Make sure the filename/case matches exactly (NATEX.py vs natex.py)
CMD ["bokeh", "serve", "NATEX.py", "--address", "0.0.0.0", "--port", "5098", "--allow-websocket-origin=*"]

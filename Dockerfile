# Use Ubuntu 20.04 as base image
FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Set working directory
WORKDIR /app

# Update system and install essential packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    wget \
    unzip \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Blender
RUN wget -O blender.tar.xz https://mirror.clarkson.edu/blender/release/Blender3.6/blender-3.6.0-linux-x64.tar.xz \
    && tar -xf blender.tar.xz \
    && mv blender-3.6.0-linux-x64 /opt/blender \
    && ln -s /opt/blender/blender /usr/local/bin/blender \
    && rm blender.tar.xz

# Install Wine for running studiomdl.exe
RUN dpkg --add-architecture i386 \
    && wget -nc https://dl.winehq.org/wine-builds/winehq.key \
    && apt-key add winehq.key \
    && add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ focal main' \
    && apt-get update \
    && apt-get install -y winehq-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Create necessary directories
RUN mkdir -p /app/backend/uploads \
    && mkdir -p /app/backend/outputs \
    && mkdir -p /usr/local/wine/cstrike

# Set up Wine environment
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win32
RUN wine --version \
    && wineboot --init \
    && winetricks -q vcrun2019

# Download and setup GoldSrc SDK studiomdl.exe (placeholder - user needs to provide this)
# Note: Due to licensing, the actual studiomdl.exe needs to be provided by the user
COPY docker/studiomdl.exe /usr/local/wine/cstrike/studiomdl.exe
RUN chmod +x /usr/local/wine/cstrike/studiomdl.exe

# Install Blender Source Tools addon (if available)
# This would typically be done by downloading from GitHub releases
RUN mkdir -p /opt/blender/3.6/scripts/addons/ \
    && wget -O source_tools.zip https://github.com/Artfunkel/BlenderSourceTools/archive/refs/heads/master.zip \
    && unzip source_tools.zip -d /tmp/ \
    && mv /tmp/BlenderSourceTools-master/io_scene_valvesource /opt/blender/3.6/scripts/addons/ \
    && rm -rf /tmp/BlenderSourceTools-master source_tools.zip

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
cd /app/backend\n\
python3 -m gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 300 app:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
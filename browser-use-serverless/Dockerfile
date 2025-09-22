# Use slim Python base image
FROM python:3.11-slim
 
# Install system dependencies for X11, VNC, noVNC, websockify, Chromium
RUN apt-get update && apt-get install -y \
    xvfb \
    netcat-openbsd \
    x11vnc \
    net-tools \
    git \
    curl \
    unzip \
    supervisor \
    python3-pip \
    chromium \
    chromium-driver \
    novnc \
    nginx \
    websockify \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*
 
# Set env so Chromium can run inside container
ENV DISPLAY=:99
ENV CHROMIUM_PATH=/usr/bin/chromium
 
# ✨ ADD: copy your unpacked extension into a stable path
# (path inside image; read-only perms are fine)
COPY app/extensions/capsolver /opt/extensions/capsolver

# Copy CapSolver API key injection script
COPY inject-capsolver-key.py /opt/inject-capsolver-key.py

RUN chown -R root:root /opt/extensions && chmod -R a+rX /opt/extensions
RUN chmod +x /opt/inject-capsolver-key.py
 
ENV EXTENSIONS_DIR=/opt/extensions/capsolver
ENV PORT=8080
# Create working dir
WORKDIR /app
RUN mkdir -p /app /var/log/uvicorn /var/log/nginx /var/log/websockify /var/log/supervisor

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy your project code
COPY app/ .
COPY app.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Fix line endings and set proper permissions for scripts
RUN sed -i 's/\r$//' /app/start-nginx.sh && chmod +x /app/start-nginx.sh
 
# Expose ports
EXPOSE 8080 443
 
# Entrypoint: supervisor manages all services

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
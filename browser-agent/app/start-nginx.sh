#!/bin/bash

# Start nginx script for supervisord

# Create nginx directories if they don't exist
mkdir -p /var/log/nginx
mkdir -p /var/run
mkdir -p /var/cache/nginx

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid. Starting nginx..."
    # Start nginx in foreground mode for supervisord
    exec nginx -g "daemon off;"
else
    echo "Nginx configuration test failed!"
    exit 1
fi
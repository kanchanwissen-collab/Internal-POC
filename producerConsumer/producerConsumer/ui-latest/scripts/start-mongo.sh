#!/bin/bash

# MongoDB Container Management Script

echo "🐳 MongoDB Container Management"
echo "==============================="

# Check if container exists
if [ "$(docker ps -aq -f name=mongo-preauth)" ]; then
    echo "📦 Container 'mongo-preauth' found"
    
    # Check if container is running
    if [ "$(docker ps -q -f name=mongo-preauth)" ]; then
        echo "✅ Container is already running"
    else
        echo "🚀 Starting container..."
        docker start mongo-preauth
        sleep 3
        echo "✅ Container started"
    fi
else
    echo "📦 Container 'mongo-preauth' not found, creating..."
    docker run -d \
        --name mongo-preauth \
        -p 27000:27017 \
        -v mongo-data:/data/db \
        -e MONGO_INITDB_ROOT_USERNAME=admin \
        -e MONGO_INITDB_ROOT_PASSWORD=password \
        mongo:latest
    
    echo "✅ Container created and started"
    sleep 5
fi

echo ""
echo "🔍 Container Status:"
docker ps -f name=mongo-preauth

echo ""
echo "🧪 Testing connection..."
npm run test:mongo

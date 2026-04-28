#!/bin/bash

set -e

APP_NAME="image-to-pdf"
IMAGE_NAME="image-to-pdf:latest"
SERVICE_NAME="image_to_pdf_service"

echo "🚀 Starting deployment for $APP_NAME ..."

# ----------------------------
# 1. Remove old Swarm service (if exists)
# ----------------------------
echo "🧹 Removing old Docker Swarm service (if exists)..."
if docker service ls | grep -q "$SERVICE_NAME"; then
    docker service rm "$SERVICE_NAME"
    echo "✔ Service removed"
else
    echo "ℹ No existing service found"
fi

# ----------------------------
# 2. Remove old container (local fallback)
# ----------------------------
echo "🧹 Removing old containers..."
docker ps -a | grep "$APP_NAME" | awk '{print $1}' | xargs -r docker rm -f || true

# ----------------------------
# 3. Remove old image
# ----------------------------
echo "🧹 Removing old image..."
if docker images | grep -q "$APP_NAME"; then
    docker rmi -f "$IMAGE_NAME" || true
    echo "✔ Old image removed"
else
    echo "ℹ No old image found"
fi

# ----------------------------
# 4. Build new image
# ----------------------------
echo "🔨 Building new Docker image..."
docker build -t $IMAGE_NAME .

# ----------------------------
# 5. Deploy to Docker Swarm
# ----------------------------
echo "🚢 Deploying to Docker Swarm..."

docker service create \
    --name $SERVICE_NAME \
    --replicas 1 \
    --publish 5613:5613 \
    $IMAGE_NAME

echo "✅ Deployment complete!"
echo "🌐 Service running on port 5613"
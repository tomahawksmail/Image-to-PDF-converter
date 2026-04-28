#!/bin/bash

set -e

APP_NAME="image-to-pdf"
REGISTRY="dregistrygui.uskoinc.com"
IMAGE_NAME="$REGISTRY/$APP_NAME:latest"
SERVICE_NAME="image_to_pdf_service"

# =========================
# ENV VARIABLES
# =========================
APP_VERSION="1.1.0"
APP_PORT="5613"

echo "🚀 Deploying $APP_NAME (version $APP_VERSION)..."

# ----------------------------
# 1. Remove old service
# ----------------------------
echo "🧹 Removing old Swarm service..."
if docker service ls | grep -q "$SERVICE_NAME"; then
    docker service rm "$SERVICE_NAME"
fi

# ----------------------------
# 2. Clean old containers/images
# ----------------------------
docker ps -a | grep "$APP_NAME" | awk '{print $1}' | xargs -r docker rm -f || true
docker images | grep "$APP_NAME" | awk '{print $3}' | xargs -r docker rmi -f || true

# ----------------------------
# 3. Build image
# ----------------------------
echo "🔨 Building image..."
docker build -t $IMAGE_NAME .

echo "🔐 Logging into registry..."
docker login $REGISTRY

echo "📤 Pushing image..."
docker push $IMAGE_NAME

echo "⏳ Ensuring image is available in registry..."
sleep 3

echo "🚢 Deploying service..."
docker service create \
    --name $SERVICE_NAME \
    --replicas 4 \
    --publish $APP_PORT:$APP_PORT \
    --env APP_VERSION=$APP_VERSION \
    --env APP_PORT=$APP_PORT \
    --with-registry-auth \
    $IMAGE_NAME
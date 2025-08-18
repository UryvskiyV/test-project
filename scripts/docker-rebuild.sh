#!/bin/bash

# Telegram LLM Bot - Docker Rebuild Script
# This script rebuilds the Docker image from scratch

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🔄 Rebuilding Telegram LLM Bot Docker image...${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Stop existing container
echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
docker-compose down 2>/dev/null || true

# Remove existing image
echo -e "${YELLOW}🗑️  Removing existing image...${NC}"
docker-compose down --rmi local 2>/dev/null || true

# Clean up build cache (optional)
echo -e "${YELLOW}🧹 Cleaning Docker build cache...${NC}"
docker builder prune -f

# Rebuild image
echo -e "${BLUE}🔨 Rebuilding image from scratch...${NC}"
docker-compose build --no-cache

# Start container
echo -e "${GREEN}▶️  Starting rebuilt container...${NC}"
docker-compose up -d

# Wait for container to start
sleep 3

# Check status
if docker-compose ps | grep -q "telegram-llm-bot.*Up"; then
    echo -e "${GREEN}✅ Bot rebuilt and started successfully!${NC}"
    echo ""
    echo "Container status:"
    docker-compose ps
else
    echo -e "${RED}❌ Failed to start rebuilt container${NC}"
    docker-compose logs
    exit 1
fi

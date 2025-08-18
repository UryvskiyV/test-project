#!/bin/bash

# Telegram LLM Bot - Docker Start Script
# This script builds and starts the bot in Docker container

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

echo -e "${BLUE}🚀 Starting Telegram LLM Bot in Docker...${NC}"
echo "Project directory: $PROJECT_DIR"

# Change to project directory
cd "$PROJECT_DIR"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env.production file not found${NC}"
    echo "Creating .env.production from .env.example..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env.production
        echo -e "${YELLOW}📝 Please edit .env.production with your actual values before running the bot${NC}"
        echo "Required variables:"
        echo "  - TELEGRAM_BOT_TOKEN"
        echo "  - OPENROUTER_API_KEY"
        read -p "Press Enter to continue or Ctrl+C to exit..."
    else
        echo -e "${RED}❌ Error: .env.example file not found${NC}"
        exit 1
    fi
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Stop existing container if running
echo -e "${YELLOW}🛑 Stopping existing container (if any)...${NC}"
docker-compose down 2>/dev/null || true

# Build and start the container
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker-compose build

echo -e "${GREEN}▶️  Starting bot container...${NC}"
docker-compose up -d

# Wait a moment for container to start
sleep 3

# Check if container is running
if docker-compose ps | grep -q "telegram-llm-bot.*Up"; then
    echo -e "${GREEN}✅ Bot started successfully!${NC}"
    echo ""
    echo "Container status:"
    docker-compose ps
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop bot: ./scripts/docker-stop.sh"
else
    echo -e "${RED}❌ Failed to start bot container${NC}"
    echo "Checking logs..."
    docker-compose logs
    exit 1
fi

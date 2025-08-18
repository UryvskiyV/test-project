#!/bin/bash

# Telegram LLM Bot - Docker Stop Script
# This script stops and cleans up the bot Docker container

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

echo -e "${BLUE}🛑 Stopping Telegram LLM Bot Docker container...${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Check if container is running
if docker-compose ps | grep -q "telegram-llm-bot.*Up"; then
    echo -e "${YELLOW}📋 Current container status:${NC}"
    docker-compose ps
    echo ""
    
    echo -e "${YELLOW}⏳ Stopping container...${NC}"
    docker-compose stop
    
    echo -e "${YELLOW}🗑️  Removing container...${NC}"
    docker-compose down
    
    echo -e "${GREEN}✅ Bot stopped successfully!${NC}"
else
    echo -e "${YELLOW}ℹ️  Container is not running${NC}"
fi

# Optional: Clean up Docker images (uncomment if needed)
# echo -e "${YELLOW}🧹 Cleaning up Docker images...${NC}"
# docker-compose down --rmi local

echo ""
echo "To start the bot again: ./scripts/docker-start.sh"
echo "To view container logs: docker-compose logs"

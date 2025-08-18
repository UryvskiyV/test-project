#!/bin/bash

# Telegram LLM Bot - Docker Logs Script
# This script shows logs from the bot Docker container

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

echo -e "${BLUE}📋 Telegram LLM Bot Docker Logs${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Check if container exists
if ! docker-compose ps | grep -q "telegram-llm-bot"; then
    echo -e "${RED}❌ Container not found. Start the bot first with: ./scripts/docker-start.sh${NC}"
    exit 1
fi

# Show logs options
echo ""
echo "Available options:"
echo "  1) Show recent logs (last 50 lines)"
echo "  2) Follow logs (real-time)"
echo "  3) Show all logs"
echo ""

read -p "Choose option (1-3) [default: 2]: " choice
choice=${choice:-2}

case $choice in
    1)
        echo -e "${GREEN}📄 Showing recent logs...${NC}"
        docker-compose logs --tail=50 telegram-llm-bot
        ;;
    2)
        echo -e "${GREEN}📡 Following logs (press Ctrl+C to stop)...${NC}"
        docker-compose logs -f telegram-llm-bot
        ;;
    3)
        echo -e "${GREEN}📚 Showing all logs...${NC}"
        docker-compose logs telegram-llm-bot
        ;;
    *)
        echo -e "${RED}❌ Invalid option${NC}"
        exit 1
        ;;
esac

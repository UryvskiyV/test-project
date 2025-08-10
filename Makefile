.PHONY: help install install-dev run test lint format clean

# Help command
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  run          - Run the bot"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean cache files"

# Install production dependencies
install:
	uv sync --frozen

# Install development dependencies
install-dev:
	uv sync --frozen --all-extras

# Run the bot
run:
	uv run python src/main.py

# Run tests
test:
	uv run pytest

# Run linting
lint:
	uv run ruff check .
	uv run black --check .

# Format code
format:
	uv run black .
	uv run ruff check --fix .

# Clean cache files
clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf dist/
	rm -rf build/

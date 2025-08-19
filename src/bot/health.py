"""Health check endpoint for cloud deployment monitoring.

This module provides a simple HTTP health check endpoint that cloud platforms
like Render.com can use to monitor the bot's status.
"""

import asyncio
from aiohttp import web
from aiohttp.web import Application, Response
import time
import json
from typing import Dict, Any

from src.logging_config import get_logger

logger = get_logger(__name__)

# Global variables to track bot status
_bot_start_time = None
_bot_status = "starting"
_last_telegram_check = None


def set_bot_status(status: str) -> None:
    """Set the current bot status.
    
    Args:
        status: Status string (starting, running, error, stopped)
    """
    global _bot_status, _bot_start_time
    _bot_status = status
    if status == "running" and _bot_start_time is None:
        _bot_start_time = time.time()
    logger.info(f"Bot status changed to: {status}")


def update_telegram_check() -> None:
    """Update the timestamp of last successful Telegram API interaction."""
    global _last_telegram_check
    _last_telegram_check = time.time()


async def health_check(request) -> Response:
    """Health check endpoint handler.
    
    Returns JSON with bot status information for monitoring.
    """
    current_time = time.time()
    uptime = current_time - _bot_start_time if _bot_start_time else 0
    
    # Check if Telegram connection is fresh (within last 5 minutes)
    telegram_healthy = (
        _last_telegram_check is not None and 
        current_time - _last_telegram_check < 300
    )
    
    health_data: Dict[str, Any] = {
        "status": _bot_status,
        "uptime_seconds": int(uptime),
        "uptime_formatted": format_uptime(uptime),
        "telegram_connection": "healthy" if telegram_healthy else "stale",
        "timestamp": current_time,
        "version": "1.0.0"
    }
    
    # Determine HTTP status code
    if _bot_status == "running" and telegram_healthy:
        status_code = 200
    elif _bot_status == "starting":
        status_code = 503  # Service Unavailable
    else:
        status_code = 500  # Internal Server Error
    
    logger.debug(f"Health check requested - Status: {_bot_status}, Code: {status_code}")
    
    return Response(
        text=json.dumps(health_data, indent=2),
        status=status_code,
        content_type="application/json"
    )


def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format.
    
    Args:
        seconds: Uptime in seconds
        
    Returns:
        Formatted uptime string
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


async def create_health_server(port: int = 8000) -> Application:
    """Create HTTP server for health checks.
    
    Args:
        port: Port to run the health server on
        
    Returns:
        Configured aiohttp Application
    """
    app = Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)  # Root path also returns health
    
    logger.info(f"Health check server configured on port {port}")
    return app


async def start_health_server(port: int = 8000) -> None:
    """Start the health check HTTP server.
    
    Args:
        port: Port to run the server on
    """
    try:
        app = await create_health_server(port)
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"Health check server started on http://0.0.0.0:{port}/health")
        
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        raise

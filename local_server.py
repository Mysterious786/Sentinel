"""
Local development server for Sentinel
Runs the dashboard API locally for development and demo
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from aiohttp import web, web_runner
from aiohttp.web import middleware
from aiohttp_cors import setup as setup_cors, ResourceOptions
import json
from datetime import datetime
from uuid import UUID

# Import Sentinel components
from src.sentinel_agent import sentinel_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_for_json(obj):
    """Convert objects to JSON-serializable format"""
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(item) for item in obj]
    elif hasattr(obj, '__str__') and not isinstance(obj, str):
        # Convert any object with __str__ method that's not already a string
        return str(obj)
    else:
        return obj


@middleware
async def cors_handler(request, handler):
    """CORS middleware for local development"""
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        response = web.Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response
    
    # Handle actual requests
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response


async def handle_dashboard(request):
    """Handle dashboard data request"""
    try:
        dashboard_data = await sentinel_agent.get_dashboard_data()
        clean_data = convert_for_json(dashboard_data)
        
        return web.json_response({
            "success": True,
            "data": clean_data
        })
    
    except Exception as e:
        logger.error(f"Dashboard endpoint error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def handle_events(request):
    """Handle events list request"""
    try:
        # Parse query parameters
        hours_back = int(request.query.get('hours', 24))
        limit = int(request.query.get('limit', 50))
        
        from src.database import db
        
        # Get recent decisions (which include event details)
        recent_decisions = await db.get_recent_decisions(hours_back=hours_back)
        
        # Limit results
        limited_results = recent_decisions[:limit]
        clean_results = convert_for_json(limited_results)
        
        return web.json_response({
            "success": True,
            "events": clean_results,
            "total": len(recent_decisions),
            "limited_to": len(limited_results)
        })
    
    except Exception as e:
        logger.error(f"Events endpoint error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def handle_simulate(request):
    """Handle event simulation request"""
    try:
        # Parse request body
        data = await request.json()
        
        # Use provided event data or generate demo data
        if "event_data" in data:
            event_data = data["event_data"]
        else:
            # Generate a sample suspicious event
            import random
            
            suspicious_ips = [
                "203.0.113.15",  # Suspicious foreign IP
                "198.51.100.42", # Previously flagged IP
                "192.0.2.100"    # Unusual source
            ]
            
            event_data = {
                "event_type": "authentication",
                "action": "login_attempt",
                "source_ip": random.choice(suspicious_ips),
                "username": data.get("username", "demo_user"),
                "timestamp": datetime.utcnow().isoformat(),
                "auth": {
                    "success": False,
                    "method": "password",
                    "attempts": random.randint(1, 5)
                },
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "geo_location": {
                    "country": "Unknown",
                    "city": "Unknown"
                }
            }
        
        # Process the event through Sentinel
        result = await sentinel_agent.process_event(event_data)
        
        return web.json_response({
            "success": True,
            "simulation_result": result,
            "simulated_event": event_data
        })
    
    except Exception as e:
        logger.error(f"Simulation endpoint error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def handle_status(request):
    """Handle status check request"""
    try:
        from src.database import db
        
        # Check database connectivity
        db_status = "connected" if db.pool else "disconnected"
        
        # Get basic stats if connected
        if db.pool:
            async with db.pool.acquire() as conn:
                event_count = await conn.fetchval("SELECT COUNT(*) FROM events")
                user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
                decision_count = await conn.fetchval("SELECT COUNT(*) FROM decisions")
        else:
            event_count = user_count = decision_count = 0
        
        status_data = {
            "agent_status": "active" if sentinel_agent.initialized else "initializing",
            "database_status": db_status,
            "statistics": {
                "total_events": event_count,
                "total_users": user_count,
                "total_decisions": decision_count
            },
            "threshold": sentinel_agent.threat_threshold,
            "version": "1.0.0"
        }
        
        return web.json_response({
            "success": True,
            "status": status_data
        })
    
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def create_app():
    """Create and configure the web application"""
    app = web.Application(middlewares=[cors_handler])
    
    # Add routes
    app.router.add_get('/dashboard', handle_dashboard)
    app.router.add_get('/events', handle_events)
    app.router.add_post('/simulate', handle_simulate)
    app.router.add_get('/status', handle_status)
    
    # Add OPTIONS handlers for CORS preflight
    app.router.add_options('/dashboard', lambda r: web.Response())
    app.router.add_options('/events', lambda r: web.Response())
    app.router.add_options('/simulate', lambda r: web.Response())
    app.router.add_options('/status', lambda r: web.Response())
    
    # Health check
    app.router.add_get('/health', lambda r: web.json_response({"status": "healthy"}))
    
    # Initialize Sentinel Agent
    await sentinel_agent.initialize()
    
    return app


async def main():
    """Main server entry point"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if we have database connection
    db_connection = os.getenv('CRDB_CONNECTION_STRING')
    if not db_connection:
        print("⚠️  No CockroachDB connection string found.")
        print("   Set CRDB_CONNECTION_STRING in .env file or environment")
        print("   The server will run in demo mode with mock data.")
        print()
    
    # Create and start the application
    app = await create_app()
    
    # Configure the runner
    runner = web_runner.AppRunner(app)
    await runner.setup()
    
    # Start the server
    port = int(os.getenv('PORT', 8000))
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    print("🛡️  Sentinel Development Server")
    print("=" * 40)
    print(f"📡 API Server: http://localhost:{port}")
    print(f"🔍 Health Check: http://localhost:{port}/health")
    print(f"📊 Dashboard API: http://localhost:{port}/dashboard")
    print()
    print("Available endpoints:")
    print("  GET  /dashboard  - Dashboard data")
    print("  GET  /events     - Recent events")
    print("  GET  /status     - Agent status")
    print("  POST /simulate   - Simulate events")
    print()
    print("To start the frontend:")
    print("  cd frontend && npm install && npm start")
    print()
    print("Press Ctrl+C to stop the server")
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
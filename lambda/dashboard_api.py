"""
AWS Lambda function for dashboard API
Provides real-time data for the Sentinel dashboard
"""
import json
import asyncio
import logging
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sentinel_agent import sentinel_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """
    Lambda entry point for dashboard API
    
    Supported endpoints:
    - GET /dashboard - Get dashboard data
    - GET /events - Get recent events
    - GET /status - Get agent status
    - POST /simulate - Simulate a security event (for demo)
    """
    
    try:
        logger.info(f"Dashboard API called: {json.dumps(event, default=str)}")
        
        # Run the async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(handle_request_async(event, context))
            return result
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Dashboard API failed: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": str(e),
                "success": False
            })
        }


async def handle_request_async(event, context):
    """Handle API request asynchronously"""
    
    # Initialize the agent
    await sentinel_agent.initialize()
    
    # Extract request details
    path = event.get("path", "/")
    method = event.get("httpMethod", "GET")
    
    logger.info(f"Handling {method} {path}")
    
    # Route the request
    if path == "/dashboard" and method == "GET":
        return await handle_get_dashboard()
    elif path == "/events" and method == "GET":
        return await handle_get_events(event)
    elif path == "/status" and method == "GET":
        return await handle_get_status()
    elif path == "/simulate" and method == "POST":
        return await handle_simulate_event(event)
    else:
        return {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Endpoint not found",
                "path": path,
                "method": method
            })
        }


async def handle_get_dashboard():
    """Get comprehensive dashboard data"""
    try:
        dashboard_data = await sentinel_agent.get_dashboard_data()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "data": dashboard_data
            }, default=str)
        }
    
    except Exception as e:
        logger.error(f"Dashboard data fetch failed: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }


async def handle_get_events(event):
    """Get recent events with optional filtering"""
    try:
        # Parse query parameters
        query_params = event.get("queryStringParameters", {}) or {}
        hours_back = int(query_params.get("hours", 24))
        limit = int(query_params.get("limit", 50))
        
        from database import db
        
        # Get recent decisions (which include event details)
        recent_decisions = await db.get_recent_decisions(hours_back=hours_back)
        
        # Limit results
        limited_results = recent_decisions[:limit]
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "events": limited_results,
                "total": len(recent_decisions),
                "limited_to": len(limited_results)
            }, default=str)
        }
    
    except Exception as e:
        logger.error(f"Events fetch failed: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }


async def handle_get_status():
    """Get agent status and health"""
    try:
        from database import db
        
        # Check database connectivity
        db_status = "connected" if db.pool else "disconnected"
        
        # Get basic stats
        async with db.pool.acquire() as conn:
            event_count = await conn.fetchval("SELECT COUNT(*) FROM events")
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            decision_count = await conn.fetchval("SELECT COUNT(*) FROM decisions")
        
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
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "status": status_data
            }, default=str)
        }
    
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }


async def handle_simulate_event(event):
    """Simulate a security event for demonstration"""
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        
        # Use provided event data or generate demo data
        if "event_data" in body:
            event_data = body["event_data"]
        else:
            # Generate a sample suspicious event
            from datetime import datetime
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
                "username": body.get("username", "demo_user"),
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
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "simulation_result": result,
                "simulated_event": event_data
            }, default=str)
        }
    
    except Exception as e:
        logger.error(f"Event simulation failed: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }
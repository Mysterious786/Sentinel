"""
Database setup script for Sentinel
Sets up CockroachDB schema and initial data
"""
import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta
import json
import random

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import db
from embedding_service import embedding_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_database():
    """Set up database schema and sample data"""
    try:
        logger.info("Starting database setup...")
        
        # Initialize database connection
        await db.initialize()
        
        # Create schema
        logger.info("Creating database schema...")
        await db.setup_schema()
        
        # Create sample users and events for demo
        logger.info("Creating sample data...")
        await create_sample_data()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    finally:
        await db.close()


async def create_sample_data():
    """Create sample users and events for demonstration"""
    
    # Sample users
    users = [
        "alice.johnson",
        "bob.smith", 
        "charlie.brown",
        "diana.prince",
        "eve.adams"
    ]
    
    # Create users with baseline embeddings
    user_ids = {}
    for username in users:
        # Create a baseline embedding (in production, this would be learned from behavior)
        baseline_text = f"normal user behavior for {username}"
        baseline_embedding = await embedding_service.generate_embedding(baseline_text)
        
        user_id = await db.insert_user(username, baseline_embedding)
        user_ids[username] = user_id
        logger.info(f"Created user: {username}")
    
    # Sample event types and sources
    event_types = ["authentication", "web_request", "file_access", "api_call", "network"]
    actions = ["login_attempt", "GET", "POST", "file_read", "file_write", "connect"]
    normal_ips = ["192.168.1.100", "10.0.0.50", "172.16.0.25"]
    suspicious_ips = ["203.0.113.15", "198.51.100.42", "192.0.2.100", "185.220.100.240"]
    
    # Create historical events (simulate 30 days of activity)
    base_time = datetime.utcnow() - timedelta(days=30)
    
    events_created = 0
    
    for day in range(30):
        current_date = base_time + timedelta(days=day)
        
        # Normal events (80% of traffic)
        for _ in range(random.randint(50, 100)):
            event_data = {
                "event_type": random.choice(event_types),
                "action": random.choice(actions),
                "source_ip": random.choice(normal_ips),
                "username": random.choice(users),
                "timestamp": (current_date + timedelta(
                    hours=random.randint(8, 18),
                    minutes=random.randint(0, 59)
                )).isoformat(),
                "auth": {"success": True, "method": "password"},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # Generate embedding and store event
            embedding = await embedding_service.generate_event_embedding(event_data)
            user_id = user_ids[event_data["username"]]
            
            await db.insert_event(
                user_id=user_id,
                event_type=event_data["event_type"],
                source_ip=event_data["source_ip"],
                action=event_data["action"],
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                raw_log=event_data,
                embedding=embedding
            )
            events_created += 1
        
        # Suspicious events (20% of traffic, more recent = more suspicious)
        if day > 15:  # More suspicious activity in recent days
            for _ in range(random.randint(5, 15)):
                event_data = {
                    "event_type": "authentication",
                    "action": "login_attempt", 
                    "source_ip": random.choice(suspicious_ips),
                    "username": random.choice(users),
                    "timestamp": (current_date + timedelta(
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )).isoformat(),
                    "auth": {
                        "success": random.choice([False, False, False, True]),  # Mostly failed attempts
                        "method": "password",
                        "attempts": random.randint(3, 10)
                    },
                    "user_agent": random.choice([
                        "curl/7.68.0",  # Automated tools
                        "python-requests/2.25.1",
                        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"  # Old browser
                    ]),
                    "geo_location": {
                        "country": random.choice(["CN", "RU", "KP", "IR"]),  # Suspicious countries
                        "city": "Unknown"
                    }
                }
                
                # Generate embedding and store event
                embedding = await embedding_service.generate_event_embedding(event_data)
                user_id = user_ids[event_data["username"]]
                
                await db.insert_event(
                    user_id=user_id,
                    event_type=event_data["event_type"],
                    source_ip=event_data["source_ip"],
                    action=event_data["action"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    raw_log=event_data,
                    embedding=embedding
                )
                events_created += 1
    
    logger.info(f"Created {events_created} sample events")
    
    # Create some sample decisions (as if the agent had been running)
    logger.info("Creating sample agent decisions...")
    
    # Get some recent events to create decisions for
    recent_events_query = """
    SELECT event_id, embedding, source_ip, event_type 
    FROM events 
    WHERE timestamp > $1 
    LIMIT 20
    """
    
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    
    async with db.pool.acquire() as conn:
        recent_events = await conn.fetch(recent_events_query, recent_cutoff)
    
    decisions_created = 0
    for event in recent_events:
        # Simulate agent decisions
        if event["source_ip"] in suspicious_ips:
            threat_score = random.uniform(6.0, 9.5)
            reasoning = "Suspicious IP address with history of failed authentication attempts"
            action = random.choice(["alert", "block_ip"])
        else:
            threat_score = random.uniform(0.5, 3.0)
            reasoning = "Normal user behavior pattern"
            action = "monitor"
        
        await db.insert_decision(
            event_id=str(event["event_id"]),
            threat_score=threat_score,
            reasoning=reasoning,
            action_taken=action,
            outcome="success"
        )
        decisions_created += 1
    
    logger.info(f"Created {decisions_created} sample decisions")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Ensure we have the connection string
    if not os.getenv('CRDB_CONNECTION_STRING'):
        print("Error: CRDB_CONNECTION_STRING environment variable not set")
        print("Please set it to your CockroachDB connection string")
        sys.exit(1)
    
    # Run setup
    asyncio.run(setup_database())
"""
Database module for Sentinel - CockroachDB operations
"""
import os
import asyncio
import asyncpg
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class SentinelDatabase:
    """Database interface for Sentinel threat hunter"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv('CRDB_CONNECTION_STRING')
        self.pool = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def setup_schema(self):
        """Create database schema if it doesn't exist"""
        schema_sql = """
        -- Users with baseline embeddings
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username STRING UNIQUE,
            baseline_embedding FLOAT8[],
            risk_score FLOAT DEFAULT 0.0,
            created_at TIMESTAMPTZ DEFAULT now()
        );

        -- Events (the core memory)
        CREATE TABLE IF NOT EXISTS events (
            event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(user_id),
            event_type STRING,
            source_ip INET,
            action STRING,
            timestamp TIMESTAMPTZ,
            raw_log JSONB,
            embedding FLOAT8[],
            created_at TIMESTAMPTZ DEFAULT now()
        );

        -- Regular index for similarity search (will use array operations)
        CREATE INDEX IF NOT EXISTS events_timestamp_idx 
        ON events (timestamp DESC);
        
        -- Index on event type for performance
        CREATE INDEX IF NOT EXISTS events_type_idx 
        ON events (event_type);

        -- Decisions and actions taken by Sentinel
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id UUID REFERENCES events(event_id),
            threat_score FLOAT,
            reasoning TEXT,
            action_taken STRING,
            outcome STRING,
            created_at TIMESTAMPTZ DEFAULT now()
        );

        -- Anomaly clusters for pattern recognition
        CREATE TABLE IF NOT EXISTS anomaly_clusters (
            cluster_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            centroid FLOAT8[],
            description TEXT,
            event_count INT DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
        logger.info("Database schema setup completed")
    
    async def insert_user(self, username: str, baseline_embedding: Optional[List[float]] = None) -> str:
        """Insert or update a user with baseline behavior"""
        query = """
        INSERT INTO users (username, baseline_embedding) 
        VALUES ($1, $2) 
        ON CONFLICT (username) 
        DO UPDATE SET baseline_embedding = EXCLUDED.baseline_embedding
        RETURNING user_id
        """
        
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval(query, username, baseline_embedding)
        return str(user_id)
    
    async def insert_event(self, user_id: str, event_type: str, source_ip: str, 
                          action: str, timestamp: datetime, raw_log: Dict[Any, Any], 
                          embedding: List[float]) -> str:
        """Insert a new security event"""
        query = """
        INSERT INTO events 
        (user_id, event_type, source_ip, action, timestamp, raw_log, embedding)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING event_id
        """
        
        async with self.pool.acquire() as conn:
            event_id = await conn.fetchval(
                query, user_id, event_type, source_ip, action, 
                timestamp, json.dumps(raw_log), embedding
            )
        return str(event_id)
    
    async def find_similar_events(self, embedding: List[float], 
                                 days_back: int = 90, limit: int = 10) -> List[Dict]:
        """Find similar events using vector similarity search"""
        query = """
        SELECT 
            event_id,
            user_id,
            event_type,
            source_ip,
            action,
            timestamp,
            raw_log,
            embedding <-> $1 as distance
        FROM events 
        WHERE timestamp > $2
        ORDER BY distance 
        LIMIT $3
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, embedding, cutoff_date, limit)
        
        return [dict(row) for row in rows]
    
    async def insert_decision(self, event_id: str, threat_score: float, 
                            reasoning: str, action_taken: str, 
                            outcome: Optional[str] = None) -> str:
        """Record an agent decision"""
        query = """
        INSERT INTO decisions 
        (event_id, threat_score, reasoning, action_taken, outcome)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING decision_id
        """
        
        async with self.pool.acquire() as conn:
            decision_id = await conn.fetchval(
                query, event_id, threat_score, reasoning, action_taken, outcome
            )
        return str(decision_id)
    
    async def get_user_baseline(self, username: str) -> Optional[List[float]]:
        """Get user's baseline behavior embedding"""
        query = "SELECT baseline_embedding FROM users WHERE username = $1"
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, username)
        
        return result
    
    async def update_user_risk_score(self, username: str, risk_score: float):
        """Update user's risk score based on recent activity"""
        query = """
        UPDATE users 
        SET risk_score = $2 
        WHERE username = $1
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, username, risk_score)
    
    async def get_recent_decisions(self, hours_back: int = 24) -> List[Dict]:
        """Get recent agent decisions for analysis"""
        query = """
        SELECT 
            d.decision_id,
            d.threat_score,
            d.reasoning,
            d.action_taken,
            d.outcome,
            d.created_at,
            e.event_type,
            e.source_ip,
            u.username
        FROM decisions d
        JOIN events e ON d.event_id = e.event_id
        JOIN users u ON e.user_id = u.user_id
        WHERE d.created_at > $1
        ORDER BY d.created_at DESC
        """
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, cutoff_time)
        
        return [dict(row) for row in rows]
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")


# Singleton instance for application use
db = SentinelDatabase()
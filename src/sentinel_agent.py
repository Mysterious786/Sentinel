"""
Main Sentinel Agent - Orchestrates the threat hunting workflow
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from .database import db
from .embedding_service import embedding_service
from .reasoning_agent import reasoning_agent
from .action_executor import action_executor

logger = logging.getLogger(__name__)


class SentinelAgent:
    """Main agent class that orchestrates the threat hunting workflow"""
    
    def __init__(self):
        self.threat_threshold = 5.0  # Threshold for taking action
        self.initialized = False
    
    async def initialize(self):
        """Initialize the agent and all its components"""
        if self.initialized:
            return
        
        logger.info("Initializing Sentinel Agent...")
        
        # Initialize database connection
        await db.initialize()
        await db.setup_schema()
        
        self.initialized = True
        logger.info("Sentinel Agent initialization complete")
    
    async def process_event(self, event_data: Dict[Any, Any]) -> Dict[str, Any]:
        """
        Main workflow: Process a security event through the complete pipeline
        
        Args:
            event_data: Raw security event data
            
        Returns:
            Dictionary containing processing results and actions taken
        """
        
        if not self.initialized:
            await self.initialize()
        
        start_time = datetime.utcnow()
        result = {
            "event_id": None,
            "threat_score": 0.0,
            "action_taken": "none",
            "reasoning": "",
            "processing_time_ms": 0,
            "success": False
        }
        
        try:
            logger.info(f"Processing event: {event_data.get('event_type')} from {event_data.get('source_ip')}")
            
            # Step 1: Generate embedding for the event
            logger.debug("Step 1: Generating event embedding")
            embedding = await embedding_service.generate_event_embedding(event_data)
            
            # Step 2: Ensure user exists and get baseline
            username = event_data.get('username', 'unknown')
            user_baseline = await db.get_user_baseline(username)
            
            if not user_baseline:
                logger.info(f"Creating new user profile for: {username}")
                user_id = await db.insert_user(username)
            else:
                # Get user_id for existing user
                async with db.pool.acquire() as conn:
                    user_id = await conn.fetchval("SELECT user_id FROM users WHERE username = $1", username)
            
            # Step 3: Store the event
            logger.debug("Step 3: Storing event in database")
            event_id = await db.insert_event(
                user_id=str(user_id),
                event_type=event_data.get('event_type', 'unknown'),
                source_ip=event_data.get('source_ip', '0.0.0.0'),
                action=event_data.get('action', 'unknown'),
                timestamp=datetime.fromisoformat(event_data.get('timestamp', datetime.utcnow().isoformat())),
                raw_log=event_data,
                embedding=embedding
            )
            result["event_id"] = event_id
            
            # Step 4: Find similar historical events
            logger.debug("Step 4: Finding similar historical events")
            similar_events = await db.find_similar_events(embedding, days_back=90, limit=10)
            
            # Step 5: Analyze threat using AI reasoning
            logger.debug("Step 5: Analyzing threat with AI agent")
            threat_score, reasoning, recommended_action = await reasoning_agent.analyze_threat(
                current_event=event_data,
                similar_events=similar_events,
                user_baseline={"baseline_embedding": user_baseline} if user_baseline else None
            )
            
            result["threat_score"] = threat_score
            result["reasoning"] = reasoning
            
            # Step 6: Execute action if threat score is above threshold
            action_result = {"success": True, "message": "No action required"}
            
            if threat_score >= self.threat_threshold:
                logger.info(f"Threat score {threat_score} exceeds threshold {self.threat_threshold}. Taking action: {recommended_action}")
                action_result = await action_executor.execute_action(
                    action=recommended_action,
                    event_data={**event_data, "event_id": event_id},
                    reasoning=reasoning
                )
                result["action_taken"] = recommended_action
            else:
                logger.info(f"Threat score {threat_score} below threshold. Monitoring only.")
                result["action_taken"] = "monitor"
            
            # Step 7: Record the decision
            logger.debug("Step 7: Recording agent decision")
            await db.insert_decision(
                event_id=event_id,
                threat_score=threat_score,
                reasoning=reasoning,
                action_taken=result["action_taken"],
                outcome="success" if action_result["success"] else "failed"
            )
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            result["processing_time_ms"] = processing_time
            result["success"] = True
            
            logger.info(f"Event processed successfully in {processing_time:.2f}ms. Threat score: {threat_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            end_time = datetime.utcnow()
            result["processing_time_ms"] = (end_time - start_time).total_seconds() * 1000
            result["reasoning"] = f"Processing error: {str(e)}"
            return result
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for the dashboard display"""
        try:
            # Get recent decisions
            recent_decisions = await db.get_recent_decisions(hours_back=24)
            
            # Calculate statistics
            total_events = len(recent_decisions)
            high_threat_events = len([d for d in recent_decisions if d["threat_score"] >= self.threat_threshold])
            blocked_ips = await action_executor.get_blocked_ips()
            
            # Get threat score distribution
            threat_scores = [d["threat_score"] for d in recent_decisions]
            avg_threat_score = sum(threat_scores) / len(threat_scores) if threat_scores else 0
            
            return {
                "statistics": {
                    "total_events_24h": total_events,
                    "high_threat_events": high_threat_events,
                    "average_threat_score": round(avg_threat_score, 2),
                    "blocked_ips_count": len(blocked_ips)
                },
                "recent_decisions": recent_decisions[:10],  # Latest 10
                "blocked_ips": blocked_ips,
                "agent_status": "active" if self.initialized else "initializing"
            }
        
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "statistics": {},
                "recent_decisions": [],
                "blocked_ips": [],
                "agent_status": "error"
            }
    
    async def shutdown(self):
        """Gracefully shutdown the agent"""
        logger.info("Shutting down Sentinel Agent...")
        await db.close()
        logger.info("Sentinel Agent shutdown complete")


# Singleton instance
sentinel_agent = SentinelAgent()
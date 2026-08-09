"""
Reasoning agent for Sentinel - Claude integration via Bedrock
"""
import boto3
import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ReasoningAgent:
    """AI agent for threat analysis using Claude via Bedrock"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def format_event_for_analysis(self, event: Dict[Any, Any]) -> str:
        """Format event data for Claude analysis"""
        raw_log_str = json.dumps(event.get('raw_log', {}), indent=2)
        event_type = event.get('event_type', 'unknown')
        source_ip = event.get('source_ip', 'unknown')
        action = event.get('action', 'unknown')
        timestamp = event.get('timestamp', 'unknown')
        username = event.get('username', 'unknown')
        
        formatted = f"""
Event Details:
- Type: {event_type}
- Source IP: {source_ip}
- Action: {action}
- Timestamp: {timestamp}
- User: {username}

Raw Event Data:
{raw_log_str}
"""
        return formatted
    
    def format_similar_events(self, similar_events: List[Dict[Any, Any]]) -> str:
        """Format similar events for context"""
        if not similar_events:
            return "No similar events found in recent history."
        
        formatted = "Similar Historical Events:\n\n"
        
        for i, event in enumerate(similar_events[:5], 1):  # Limit to top 5
            distance = event.get('distance', 'unknown')
            distance_str = f"{distance:.4f}" if isinstance(distance, (int, float)) else str(distance)
            raw_data_str = json.dumps(event.get('raw_log', {}), indent=2)[:200]
            event_type = event.get('event_type', 'unknown')
            source_ip = event.get('source_ip', 'unknown')
            action = event.get('action', 'unknown')
            timestamp = event.get('timestamp', 'unknown')
            
            formatted += f"""
Event #{i} (Distance: {distance_str}):
- Type: {event_type}
- Source IP: {source_ip}
- Action: {action}
- Timestamp: {timestamp}
- Raw Data: {raw_data_str}...

"""
        return formatted
    
    async def analyze_threat(self, current_event: Dict[Any, Any], 
                           similar_events: List[Dict[Any, Any]],
                           user_baseline: Dict[Any, Any] = None) -> Tuple[float, str, str]:
        """
        Analyze threat level of current event given historical context
        
        Returns:
            Tuple of (threat_score, reasoning, recommended_action)
        """
        
        # Construct the analysis prompt
        user_baseline_str = json.dumps(user_baseline or {}, indent=2) if user_baseline else "No baseline available"
        
        prompt = """You are Sentinel, an AI security analyst specializing in Advanced Persistent Threat (APT) detection. Your job is to analyze security events in the context of historical patterns to identify coordinated attacks that unfold over weeks or months.

CURRENT EVENT TO ANALYZE:
""" + self.format_event_for_analysis(current_event) + """

HISTORICAL CONTEXT:
""" + self.format_similar_events(similar_events) + """

USER BASELINE:
""" + user_baseline_str + """

ANALYSIS INSTRUCTIONS:
1. Look for patterns that suggest this event is part of a larger campaign:
   - IP address reuse across time periods
   - Similar attack vectors with slight variations
   - Gradual escalation of privileges or access attempts
   - Timing patterns that suggest coordinated activity

2. Consider the following threat indicators:
   - Unusual source IPs for this user
   - Authentication failures followed by success
   - Access to sensitive resources
   - Deviation from normal user behavior patterns
   - Geographic anomalies

3. Provide a threat score from 0-10:
   - 0-2: Normal behavior, no action needed
   - 3-4: Slightly suspicious, monitor
   - 5-6: Moderate threat, alert security team
   - 7-8: High threat, block and investigate
   - 9-10: Critical threat, immediate response required

4. Recommend one of these actions:
   - "monitor": Continue observing, no immediate action
   - "alert": Notify security operations center
   - "block_ip": Block the source IP address
   - "block_user": Temporarily suspend user account
   - "escalate": Immediate security team investigation

RESPOND IN THIS EXACT JSON FORMAT:
{
    "threat_score": <0-10>,
    "reasoning": "<detailed explanation of your analysis>",
    "recommended_action": "<one of: monitor, alert, block_ip, block_user, escalate>",
    "confidence": <0-1>,
    "key_indicators": ["<indicator1>", "<indicator2>", "..."]
}"""

        try:
            # Call Claude via Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            content = response_body["content"][0]["text"]
            
            # Parse the JSON response
            try:
                analysis = json.loads(content)
                threat_score = float(analysis.get("threat_score", 0))
                reasoning = analysis.get("reasoning", "Analysis failed")
                action = analysis.get("recommended_action", "monitor")
                
                logger.info(f"Threat analysis complete. Score: {threat_score}, Action: {action}")
                return threat_score, reasoning, action
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Claude response: {content}")
                return 0.0, "Analysis parsing failed", "monitor"
            
        except ClientError as e:
            logger.error(f"AWS Bedrock error during analysis: {e}")
            # Fallback to simple rule-based analysis for demo
            return self._fallback_analysis(current_event, similar_events)
        except Exception as e:
            logger.error(f"Threat analysis error: {e}")
            # Fallback to simple rule-based analysis for demo
            return self._fallback_analysis(current_event, similar_events)
    
    def _fallback_analysis(self, current_event: Dict[Any, Any], 
                          similar_events: List[Dict[Any, Any]]) -> Tuple[float, str, str]:
        """Fallback rule-based threat analysis for demo when AI is unavailable"""
        threat_score = 0.0
        reasoning_parts = []
        
        # Check for suspicious indicators
        source_ip = current_event.get('source_ip', '')
        event_type = current_event.get('event_type', '')
        
        # Suspicious IP ranges (demo IPs)
        if source_ip in ['203.0.113.15', '198.51.100.42', '192.0.2.100']:
            threat_score += 3.0
            reasoning_parts.append(f"Suspicious IP address detected: {source_ip}")
        
        # Authentication failures
        auth_info = current_event.get('auth', {})
        if not auth_info.get('success', True):
            threat_score += 2.0
            attempts = auth_info.get('attempts', 1)
            if attempts > 3:
                threat_score += 1.0
                reasoning_parts.append(f"Multiple failed authentication attempts: {attempts}")
            else:
                reasoning_parts.append("Failed authentication detected")
        
        # Check for similar events in history
        if similar_events:
            similar_count = len([e for e in similar_events if e.get('distance', 1.0) < 0.3])
            if similar_count >= 3:
                threat_score += 2.0
                reasoning_parts.append(f"Found {similar_count} similar historical events suggesting pattern")
        
        # Determine action based on score
        if threat_score >= 7.0:
            action = "block_ip"
        elif threat_score >= 5.0:
            action = "alert"
        elif threat_score >= 3.0:
            action = "monitor"
        else:
            action = "monitor"
        
        if not reasoning_parts:
            reasoning_parts.append("Normal user behavior pattern detected")
        
        reasoning = "FALLBACK ANALYSIS: " + ". ".join(reasoning_parts) + f". Calculated threat score: {threat_score}/10"
        
        return threat_score, reasoning, action

    async def generate_alert_message(self, event: Dict[Any, Any], 
                                   threat_score: float, reasoning: str) -> str:
        """Generate a human-readable alert message"""
        event_type = event.get('event_type', 'Unknown')
        source_ip = event.get('source_ip', 'Unknown')
        username = event.get('username', 'Unknown')
        timestamp = event.get('timestamp', 'Unknown')
        event_id = event.get('event_id', 'Unknown')
        
        return f"""
🚨 SENTINEL THREAT ALERT 🚨

Threat Score: {threat_score}/10
Event Type: {event_type}
Source IP: {source_ip}
User: {username}
Timestamp: {timestamp}

Analysis:
{reasoning}

This alert was generated by Sentinel's AI agent based on historical pattern analysis.
Event ID: {event_id}
"""


# Singleton instance
reasoning_agent = ReasoningAgent()
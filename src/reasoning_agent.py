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
        self.model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
    
    def format_event_for_analysis(self, event: Dict[Any, Any]) -> str:
        """Format event data for Claude analysis"""
        formatted = f"""
Event Details:
- Type: {event.get('event_type', 'unknown')}
- Source IP: {event.get('source_ip', 'unknown')}
- Action: {event.get('action', 'unknown')}
- Timestamp: {event.get('timestamp', 'unknown')}
- User: {event.get('username', 'unknown')}

Raw Event Data:
{json.dumps(event.get('raw_log', {}), indent=2)}
"""
        return formatted
    
    def format_similar_events(self, similar_events: List[Dict[Any, Any]]) -> str:
        """Format similar events for context"""
        if not similar_events:
            return "No similar events found in recent history."
        
        formatted = "Similar Historical Events:\n\n"
        
        for i, event in enumerate(similar_events[:5], 1):  # Limit to top 5
            formatted += f"""
Event #{i} (Distance: {event.get('distance', 'unknown'):.4f}):
- Type: {event.get('event_type', 'unknown')}
- Source IP: {event.get('source_ip', 'unknown')}
- Action: {event.get('action', 'unknown')}
- Timestamp: {event.get('timestamp', 'unknown')}
- Raw Data: {json.dumps(event.get('raw_log', {}), indent=2)[:200]}...

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
        prompt = f"""You are Sentinel, an AI security analyst specializing in Advanced Persistent Threat (APT) detection. Your job is to analyze security events in the context of historical patterns to identify coordinated attacks that unfold over weeks or months.

CURRENT EVENT TO ANALYZE:
{self.format_event_for_analysis(current_event)}

HISTORICAL CONTEXT:
{self.format_similar_events(similar_events)}

USER BASELINE:
{json.dumps(user_baseline or {}, indent=2) if user_baseline else "No baseline available"}

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
            return 0.0, f"Bedrock error: {str(e)}", "monitor"
        except Exception as e:
            logger.error(f"Threat analysis error: {e}")
            return 0.0, f"Analysis error: {str(e)}", "monitor"
    
    async def generate_alert_message(self, event: Dict[Any, Any], 
                                   threat_score: float, reasoning: str) -> str:
        """Generate a human-readable alert message"""
        return f"""
🚨 SENTINEL THREAT ALERT 🚨

Threat Score: {threat_score}/10
Event Type: {event.get('event_type', 'Unknown')}
Source IP: {event.get('source_ip', 'Unknown')}
User: {event.get('username', 'Unknown')}
Timestamp: {event.get('timestamp', 'Unknown')}

Analysis:
{reasoning}

This alert was generated by Sentinel's AI agent based on historical pattern analysis.
Event ID: {event.get('event_id', 'Unknown')}
"""


# Singleton instance
reasoning_agent = ReasoningAgent()
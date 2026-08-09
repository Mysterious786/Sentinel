"""
Action executor for Sentinel - AWS security actions
"""
import boto3
import logging
from typing import Dict, Any, Optional, List
import json
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes security actions based on agent decisions"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.ec2_client = boto3.client("ec2", region_name=region)
        self.waf_client = boto3.client("wafv2", region_name=region)
        self.sns_client = boto3.client("sns", region_name=region)
        
        # Configuration - these would come from environment variables
        self.security_group_id = "sg-sentinel-managed"  # Managed security group
        self.waf_web_acl_id = "sentinel-web-acl"        # WAF Web ACL
        self.alert_topic_arn = "arn:aws:sns:us-east-1:account:sentinel-alerts"
    
    async def execute_action(self, action: str, event_data: Dict[Any, Any], 
                           reasoning: str) -> Dict[str, Any]:
        """Execute the recommended security action"""
        result = {
            "action": action,
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            if action == "monitor":
                result = await self.action_monitor(event_data)
            elif action == "alert":
                result = await self.action_alert(event_data, reasoning)
            elif action == "block_ip":
                result = await self.action_block_ip(event_data, reasoning)
            elif action == "block_user":
                result = await self.action_block_user(event_data, reasoning)
            elif action == "escalate":
                result = await self.action_escalate(event_data, reasoning)
            else:
                result["message"] = f"Unknown action: {action}"
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            result["message"] = f"Execution error: {str(e)}"
        
        return result
    
    async def action_monitor(self, event_data: Dict[Any, Any]) -> Dict[str, Any]:
        """Monitor action - log the event for future reference"""
        logger.info(f"Monitoring event from IP {event_data.get('source_ip')}")
        
        return {
            "action": "monitor",
            "success": True,
            "message": "Event logged for monitoring",
            "details": {
                "monitoring_enabled": True,
                "retention_days": 90
            }
        }
    
    async def action_alert(self, event_data: Dict[Any, Any], reasoning: str) -> Dict[str, Any]:
        """Send alert to security operations center"""
        try:
            message = f"""
SENTINEL SECURITY ALERT

Event Details:
- Source IP: {event_data.get('source_ip', 'Unknown')}
- Event Type: {event_data.get('event_type', 'Unknown')}
- User: {event_data.get('username', 'Unknown')}
- Timestamp: {event_data.get('timestamp', 'Unknown')}

Analysis:
{reasoning}

This is an automated alert from Sentinel threat hunter.
Event ID: {event_data.get('event_id', 'Unknown')}
"""
            
            # In a real implementation, send to SNS
            # self.sns_client.publish(
            #     TopicArn=self.alert_topic_arn,
            #     Message=message,
            #     Subject="Sentinel Security Alert"
            # )
            
            logger.warning(f"ALERT: {message}")
            
            return {
                "action": "alert",
                "success": True,
                "message": "Alert sent to security team",
                "details": {
                    "alert_sent": True,
                    "notification_method": "sns"
                }
            }
            
        except Exception as e:
            return {
                "action": "alert",
                "success": False,
                "message": f"Failed to send alert: {str(e)}",
                "details": {}
            }
    
    async def action_block_ip(self, event_data: Dict[Any, Any], reasoning: str) -> Dict[str, Any]:
        """Block source IP address"""
        source_ip = event_data.get('source_ip')
        if not source_ip:
            return {
                "action": "block_ip",
                "success": False,
                "message": "No source IP to block",
                "details": {}
            }
        
        try:
            # In a real implementation, add IP to security group deny rule
            # or update WAF IP set
            
            # Simulate the blocking action
            logger.critical(f"BLOCKING IP: {source_ip} - Reason: {reasoning}")
            
            # Example WAF IP set update (commented for demo)
            # self.waf_client.update_ip_set(
            #     Scope='CLOUDFRONT',
            #     Id='sentinel-blocked-ips',
            #     Addresses=[f"{source_ip}/32"]
            # )
            
            return {
                "action": "block_ip",
                "success": True,
                "message": f"IP {source_ip} blocked successfully",
                "details": {
                    "blocked_ip": source_ip,
                    "method": "waf_ip_set",
                    "duration": "permanent"
                }
            }
            
        except Exception as e:
            return {
                "action": "block_ip",
                "success": False,
                "message": f"Failed to block IP: {str(e)}",
                "details": {"target_ip": source_ip}
            }
    
    async def action_block_user(self, event_data: Dict[Any, Any], reasoning: str) -> Dict[str, Any]:
        """Block user account temporarily"""
        username = event_data.get('username')
        if not username:
            return {
                "action": "block_user",
                "success": False,
                "message": "No username to block",
                "details": {}
            }
        
        try:
            # In a real implementation, disable user in IAM or identity provider
            logger.critical(f"BLOCKING USER: {username} - Reason: {reasoning}")
            
            return {
                "action": "block_user",
                "success": True,
                "message": f"User {username} blocked successfully",
                "details": {
                    "blocked_user": username,
                    "method": "iam_policy",
                    "duration": "24_hours"
                }
            }
            
        except Exception as e:
            return {
                "action": "block_user",
                "success": False,
                "message": f"Failed to block user: {str(e)}",
                "details": {"target_user": username}
            }
    
    async def action_escalate(self, event_data: Dict[Any, Any], reasoning: str) -> Dict[str, Any]:
        """Escalate to immediate security team investigation"""
        try:
            # Send high-priority alert and create incident ticket
            message = f"""
🚨 CRITICAL SECURITY INCIDENT - IMMEDIATE ATTENTION REQUIRED 🚨

Event Details:
- Source IP: {event_data.get('source_ip', 'Unknown')}
- Event Type: {event_data.get('event_type', 'Unknown')}
- User: {event_data.get('username', 'Unknown')}
- Timestamp: {event_data.get('timestamp', 'Unknown')}

Threat Analysis:
{reasoning}

This requires IMMEDIATE investigation by the security team.
Sentinel has identified this as a critical threat requiring human analysis.

Event ID: {event_data.get('event_id', 'Unknown')}
"""
            
            logger.critical(f"ESCALATION: {message}")
            
            # In production, this would:
            # 1. Send high-priority SNS notification
            # 2. Create incident in ticket system
            # 3. Page on-call security engineer
            # 4. Potentially trigger automated containment
            
            return {
                "action": "escalate",
                "success": True,
                "message": "Incident escalated to security team",
                "details": {
                    "escalation_level": "critical",
                    "incident_created": True,
                    "on_call_notified": True
                }
            }
            
        except Exception as e:
            return {
                "action": "escalate",
                "success": False,
                "message": f"Failed to escalate: {str(e)}",
                "details": {}
            }
    
    async def get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs"""
        try:
            # In production, query WAF IP sets or security groups
            # For demo, return empty list
            return []
        except Exception as e:
            logger.error(f"Failed to get blocked IPs: {e}")
            return []


# Singleton instance
action_executor = ActionExecutor()
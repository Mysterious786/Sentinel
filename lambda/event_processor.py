"""
AWS Lambda function for processing security events
Triggered by S3 uploads or SQS messages
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
    Lambda entry point for processing security events
    
    Expected event formats:
    1. S3 trigger: Process log files uploaded to S3
    2. SQS message: Process individual events
    3. API Gateway: Direct event submission
    """
    
    try:
        logger.info(f"Lambda triggered with event: {json.dumps(event, default=str)}")
        
        # Run the async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(process_event_async(event, context))
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(result)
            }
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
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


async def process_event_async(event, context):
    """Async processing logic"""
    
    # Initialize the agent
    await sentinel_agent.initialize()
    
    results = []
    
    try:
        # Handle different event sources
        if "Records" in event:
            # S3 or SQS event
            for record in event["Records"]:
                if record.get("eventSource") == "aws:s3":
                    # S3 upload trigger - process log file
                    result = await process_s3_event(record)
                    results.append(result)
                elif "aws:sqs" in record.get("eventSource", ""):
                    # SQS message - process individual event
                    result = await process_sqs_event(record)
                    results.append(result)
        
        elif "httpMethod" in event:
            # API Gateway direct event
            result = await process_api_event(event)
            results.append(result)
        
        else:
            # Direct lambda invocation with event data
            if "event_data" in event:
                result = await sentinel_agent.process_event(event["event_data"])
                results.append(result)
            else:
                raise ValueError("Unknown event format")
        
        return {
            "success": True,
            "results": results,
            "processed_events": len(results)
        }
    
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": results
        }


async def process_s3_event(record):
    """Process security logs uploaded to S3"""
    import boto3
    
    # Extract S3 details
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    
    logger.info(f"Processing S3 file: s3://{bucket}/{key}")
    
    try:
        # Download and parse the log file
        s3_client = boto3.client("s3")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        
        # Parse logs (assuming JSONL format for demo)
        events_processed = 0
        for line in content.strip().split("\n"):
            if line.strip():
                try:
                    log_event = json.loads(line)
                    # Convert to our event format
                    event_data = convert_log_to_event(log_event)
                    await sentinel_agent.process_event(event_data)
                    events_processed += 1
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse log line: {line}")
        
        return {
            "source": "s3",
            "file": f"s3://{bucket}/{key}",
            "events_processed": events_processed
        }
    
    except Exception as e:
        logger.error(f"S3 processing failed: {e}")
        return {
            "source": "s3",
            "file": f"s3://{bucket}/{key}",
            "error": str(e)
        }


async def process_sqs_event(record):
    """Process individual event from SQS"""
    try:
        # Parse SQS message
        message_body = json.loads(record["body"])
        event_data = message_body.get("event_data", message_body)
        
        result = await sentinel_agent.process_event(event_data)
        
        return {
            "source": "sqs",
            "message_id": record.get("messageId"),
            "result": result
        }
    
    except Exception as e:
        logger.error(f"SQS processing failed: {e}")
        return {
            "source": "sqs",
            "error": str(e)
        }


async def process_api_event(event):
    """Process event from API Gateway"""
    try:
        # Parse request body
        body = json.loads(event["body"]) if event.get("body") else {}
        event_data = body.get("event_data", body)
        
        result = await sentinel_agent.process_event(event_data)
        
        return {
            "source": "api",
            "result": result
        }
    
    except Exception as e:
        logger.error(f"API processing failed: {e}")
        return {
            "source": "api",
            "error": str(e)
        }


def convert_log_to_event(log_event):
    """Convert various log formats to Sentinel event format"""
    
    # Default event structure
    event_data = {
        "event_type": "unknown",
        "source_ip": "0.0.0.0",
        "action": "unknown",
        "username": "unknown",
        "timestamp": log_event.get("timestamp", ""),
        "raw_log": log_event
    }
    
    # AWS CloudTrail format
    if "eventName" in log_event:
        event_data.update({
            "event_type": "aws_api",
            "action": log_event["eventName"],
            "source_ip": log_event.get("sourceIPAddress", "0.0.0.0"),
            "username": log_event.get("userIdentity", {}).get("userName", "unknown")
        })
    
    # VPC Flow Logs format
    elif "protocol" in log_event:
        event_data.update({
            "event_type": "network",
            "action": "connection",
            "source_ip": log_event.get("srcaddr", "0.0.0.0"),
            "username": "system"
        })
    
    # Web server logs
    elif "method" in log_event:
        event_data.update({
            "event_type": "web_request",
            "action": log_event["method"],
            "source_ip": log_event.get("client_ip", "0.0.0.0"),
            "username": log_event.get("user", "anonymous")
        })
    
    # Authentication logs
    elif "auth_result" in log_event:
        event_data.update({
            "event_type": "authentication",
            "action": "login_attempt",
            "source_ip": log_event.get("source_ip", "0.0.0.0"),
            "username": log_event.get("username", "unknown")
        })
    
    return event_data
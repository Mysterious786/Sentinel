# Sentinel Architecture

## System Overview

Sentinel is a memory-driven threat hunting agent that uses CockroachDB's distributed vector indexing to correlate security events across time. The system combines semantic embeddings, AI reasoning, and autonomous actions to detect Advanced Persistent Threats (APTs).

## Core Components

### 1. Event Processing Pipeline
```
Raw Logs → Embedding → Storage → Retrieval → Reasoning → Action
```

**Flow:**
1. **Ingestion**: Security events from various sources (S3, SQS, API)
2. **Embedding**: Convert events to 1024-dimensional vectors using Titan
3. **Storage**: Store in CockroachDB with vector indexing
4. **Retrieval**: Find similar historical events using vector similarity
5. **Reasoning**: Claude analyzes current + historical context
6. **Action**: Execute security responses (block, alert, escalate)
7. **Memory**: Store decisions for future learning

### 2. Memory Architecture

**Vector Memory**
- Every event becomes a semantic embedding
- CockroachDB vector index enables similarity search
- Historical context spans up to 90 days by default
- Recency weighting gives priority to recent events

**Memory Types**
- **Episodic**: Individual security events with full context
- **Semantic**: Vector representations for similarity matching
- **Temporal**: Time-based correlation and patterns
- **User Context**: Baseline behavior profiles per user
- **Decision Memory**: Past agent decisions and outcomes

### 3. Database Schema

```sql
-- Core tables for memory storage
users (user_id, username, baseline_embedding, risk_score)
events (event_id, user_id, event_type, source_ip, embedding, raw_log)  
decisions (decision_id, event_id, threat_score, reasoning, action_taken)
anomaly_clusters (cluster_id, centroid, description)
```

**Key Features:**
- Vector index on events.embedding for O(log n) similarity search  
- JSONB storage for flexible raw log data
- UUID primary keys for distributed scalability
- Temporal indexing for time-based queries

### 4. AI Reasoning Engine

**Claude 3.5 Haiku Integration**
- Analyzes events in context of retrieved similar events
- Provides threat scores (0-10) with detailed reasoning
- Recommends specific actions based on threat level
- Learns from past decision outcomes

**Embedding Generation** 
- Amazon Titan Embeddings v2 (1024 dimensions)
- Semantic preprocessing of event data
- Captures patterns like IP addresses, user agents, timing
- Geographic and behavioral context inclusion

### 5. Action Execution

**Response Actions**
- **Monitor**: Log and observe (0-2 threat score)
- **Alert**: Notify security team (3-6 threat score)  
- **Block IP**: Add to WAF deny list (7-8 threat score)
- **Block User**: Disable account access (8-9 threat score)
- **Escalate**: Emergency response (9-10 threat score)

**AWS Integration**
- Lambda functions for serverless execution
- IAM roles with least privilege access
- SNS for alerting and notifications
- WAF/Security Groups for IP blocking

## Deployment Architecture

### AWS Serverless Stack

```
API Gateway → Lambda Functions → Bedrock AI → CockroachDB
     ↓              ↓              ↓           ↓
Dashboard      Event Processing   Embeddings   Vector Storage
```

**Components:**
- **Lambda Functions**: Event processing and dashboard API
- **API Gateway**: HTTP endpoints for dashboard
- **S3**: Log file storage and archival  
- **SQS**: Event queue decoupling
- **Bedrock**: AI embedding and reasoning services
- **CockroachDB Cloud**: Distributed vector database

### Local Development Stack

```
React Dashboard ← HTTP → Python API Server ← PostgreSQL → CockroachDB
```

**Components:**
- **React Dashboard**: Real-time threat monitoring UI
- **Python API Server**: Local development backend  
- **CockroachDB**: Vector database (local or cloud)

## Data Flow

### 1. Event Ingestion
```
Log Sources → S3/SQS → Lambda → Preprocessing → Embedding Generation
```

### 2. Memory Storage  
```
Event + Embedding → CockroachDB → Vector Index → Retrieval Ready
```

### 3. Threat Analysis
```
New Event → Similar Events Retrieval → Claude Reasoning → Threat Score
```

### 4. Action Execution
```
Threat Score → Action Decision → AWS Services → Security Response
```

### 5. Learning Loop
```
Action Outcome → Decision Storage → Future Context → Improved Accuracy
```

## Scalability

**Horizontal Scaling**
- CockroachDB automatically distributes data across nodes
- Lambda functions scale based on event volume
- Vector indexes partition by time ranges
- S3 provides unlimited storage capacity

**Performance Optimization**
- Vector similarity search: O(log n) with proper indexing
- Event partitioning by timestamp for faster queries
- Embedding batching for high-volume ingestion  
- Decision caching to reduce AI API calls

**Cost Optimization**
- Serverless computing only charges for usage
- S3 lifecycle policies for log archival
- CockroachDB auto-scaling based on demand
- Bedrock pay-per-token pricing model

## Security Model

**Access Control**
- IAM roles with least privilege principles
- VPC isolation for database connections
- API Gateway authentication and throttling
- Encrypted storage for all sensitive data

**Data Protection**
- TLS encryption for all data in transit
- Encryption at rest in CockroachDB and S3
- No plain-text secrets in code or logs
- Audit trail for all agent actions

## Operational Model

**Monitoring**
- CloudWatch metrics for Lambda performance
- CockroachDB admin UI for database health
- Dashboard provides real-time system status
- Automated alerting for system failures

**Maintenance**
- Automated schema migrations via scripts
- Backup and recovery through CockroachDB Cloud
- Log retention and archival policies
- A/B testing for AI model improvements

## Future Enhancements

**Advanced AI Features**
- Unsupervised clustering for novel attack discovery
- Temporal sequence modeling for attack chain detection
- Multi-modal analysis (network + endpoint + cloud logs)
- Federated learning across organizations

**Platform Extensions**
- Integration with major SIEM platforms
- Custom threat intelligence feed ingestion
- Automated incident response playbooks
- Natural language query interface for investigations
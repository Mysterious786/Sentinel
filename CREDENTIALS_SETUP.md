# 🔐 Sentinel Credentials & Embeddings Setup Guide

## 🎯 Overview

Sentinel supports multiple embedding providers and databases with automatic fallback. This guide shows you how to set up credentials for maximum functionality, but **the system works without any external credentials** using local embeddings and mock data.

## 🚀 Quick Start (No Credentials Needed)

For immediate demo:
```bash
python local_server.py
```
This runs with:
- Local sentence transformer embeddings
- Mock data (no database required)
- Full functionality for demonstrations

## 📊 Embedding Provider Options

### Option 1: AWS Bedrock (Recommended for Production)
**Best choice**: High-quality embeddings, scalable, production-ready

**Setup:**
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Configure credentials
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]  
# Default region name: us-east-1
# Default output format: json
```

**Required permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        }
    ]
}
```

**Environment variables:**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Option 2: OpenAI (Alternative)
**Good choice**: High-quality embeddings, easy setup

**Setup:**
1. Get API key from https://platform.openai.com/api-keys
2. Install OpenAI package: `pip install openai`

**Environment variables:**
```bash
export OPENAI_API_KEY=sk-your-openai-key
```

### Option 3: Local Embeddings (Default Fallback)
**Best for demos**: No credentials needed, works offline

**Setup:**
```bash
pip install sentence-transformers
```

The system automatically downloads the `all-MiniLM-L6-v2` model on first use.

## 🗄️ Database Options

### Option 1: CockroachDB Cloud (Recommended)
**Best choice**: Full vector indexing, distributed, production-ready

**Setup:**
1. **Create Account**: Visit https://cockroachlabs.cloud/
2. **Create Cluster**: 
   - Select "Serverless" for free tier
   - Choose region (us-east-1 recommended)
   - Note connection details

3. **Get Connection String**:
   ```
   postgresql://username:password@host:port/database?sslmode=require
   ```

4. **Set Environment Variable**:
   ```bash
   export CRDB_CONNECTION_STRING="postgresql://username:password@host:port/database?sslmode=require"
   ```

### Option 2: Local PostgreSQL
**Good for development**: Local control, no cloud dependencies

**Setup:**
```bash
# Install PostgreSQL
brew install postgresql

# Start service
brew services start postgresql

# Create database
createdb sentinel_dev

# Connection string
export CRDB_CONNECTION_STRING="postgresql://localhost/sentinel_dev"
```

**Note**: Local PostgreSQL won't have vector indexing, but Sentinel will adapt.

### Option 3: Mock Data (Default Fallback)
**Best for demos**: No database needed, instant startup

No setup required - Sentinel automatically uses mock data if no database is configured.

## 🔧 Complete .env File Setup

Create `.env` file in project root:

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

**Full .env example:**
```bash
# Database (choose one)
CRDB_CONNECTION_STRING=postgresql://username:password@host:port/database?sslmode=require
# OR for local PostgreSQL:
# CRDB_CONNECTION_STRING=postgresql://localhost/sentinel_dev

# AWS Bedrock (optional - for best embeddings)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
AWS_BEDROCK_REGION=us-east-1

# OpenAI (optional - alternative embeddings)
OPENAI_API_KEY=sk-your-openai-key

# AWS Services (optional - for cloud deployment)
AWS_S3_BUCKET=sentinel-logs-bucket
AWS_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:account:sentinel-alerts

# Agent Configuration
SENTINEL_THREAT_THRESHOLD=5.0
SENTINEL_LOG_LEVEL=INFO
```

## 🎚️ Provider Priority & Fallback

Sentinel automatically tries providers in this order:

1. **AWS Bedrock** (if credentials configured)
2. **OpenAI** (if API key provided)
3. **Local Sentence Transformers** (always available)
4. **TF-IDF** (last resort fallback)

**Check current provider:**
```python
python -c "
import asyncio
from src.embedding_service import embedding_service
print(f'Provider: {embedding_service.provider}')
print(embedding_service.get_provider_info())
"
```

## 🧪 Test Your Setup

Run the test suite to verify everything works:

```bash
python test_sentinel.py
```

This will:
- ✅ Test embedding generation
- ✅ Verify database connection (if configured)
- ✅ Check AI reasoning
- ✅ Validate end-to-end pipeline

## 🔒 Security Best Practices

### AWS Credentials
- **Use IAM roles** in production, not access keys
- **Rotate credentials** regularly
- **Limit permissions** to only what's needed
- **Use AWS Secrets Manager** for production deployments

### Database Security
- **Use SSL/TLS** connections (sslmode=require)
- **Rotate passwords** regularly
- **Use read-only credentials** for demo/dev environments
- **Enable audit logging** in production

### API Keys
- **Never commit** API keys to version control
- **Use environment variables** or secret management
- **Monitor usage** for unexpected spikes
- **Set spending limits** on API accounts

## 🚀 Deployment Scenarios

### 1. Demo Mode (No Credentials)
```bash
# Just run - works immediately
python local_server.py
cd frontend && npm start
```

### 2. Development Mode (Local DB)
```bash
# Setup local PostgreSQL
export CRDB_CONNECTION_STRING="postgresql://localhost/sentinel_dev"
python scripts/setup_database.py
python local_server.py
```

### 3. Cloud Development (CockroachDB)
```bash
# Setup cloud database
export CRDB_CONNECTION_STRING="postgresql://user:pass@host:port/db?sslmode=require"
python scripts/setup_database.py
python local_server.py
```

### 4. Production Mode (Full AWS)
```bash
# Configure all credentials
aws configure
export CRDB_CONNECTION_STRING="..."
./scripts/deploy.sh
```

## 🆘 Troubleshooting

### "No AWS credentials found"
```bash
# Check AWS configuration
aws sts get-caller-identity

# If fails, reconfigure:
aws configure
```

### "Bedrock region not supported"
```bash
# Try different region
export AWS_BEDROCK_REGION=us-west-2
```

### "Database connection failed"
```bash
# Test connection string
python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('your-connection-string')
    await conn.close()
    print('✅ Database connection successful')
asyncio.run(test())
"
```

### "Embedding provider failed"
The system automatically falls back to local embeddings. Check logs:
```bash
python -c "
import logging
logging.basicConfig(level=logging.INFO)
from src.embedding_service import embedding_service
print(f'Active provider: {embedding_service.provider}')
"
```

## 🎯 Recommended Setup by Use Case

### Hackathon Demo
- **Embeddings**: Local (no setup)
- **Database**: Mock data (no setup)
- **Time to demo**: 0 minutes

### Development
- **Embeddings**: OpenAI (easy setup)
- **Database**: CockroachDB Cloud (free tier)
- **Time to setup**: 15 minutes

### Production
- **Embeddings**: AWS Bedrock (scalable)
- **Database**: CockroachDB Cloud (dedicated)
- **Deployment**: AWS Lambda + API Gateway
- **Time to setup**: 2-4 hours

## 📞 Support

**Need help?** Check these resources:

1. **Test your setup**: `python test_sentinel.py`
2. **Check logs**: All services log their initialization status
3. **Fallback mode**: System works without any credentials
4. **Documentation**: Each service has detailed error messages

**The beauty of Sentinel**: It works at every level, from no-credential demos to full production deployments! 🛡️
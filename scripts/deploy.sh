#!/bin/bash

# Sentinel Deployment Script
# Deploys Lambda functions and sets up AWS infrastructure

set -e

echo "🚀 Starting Sentinel deployment..."

# Configuration
LAMBDA_RUNTIME="python3.11"
LAMBDA_TIMEOUT=300
LAMBDA_MEMORY=512

# Function names
EVENT_PROCESSOR_FUNCTION="sentinel-event-processor"
DASHBOARD_API_FUNCTION="sentinel-dashboard-api"

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        echo "❌ AWS CLI not found. Please install it first."
        exit 1
    fi
    
    if ! command -v zip &> /dev/null; then
        echo "❌ zip command not found. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    echo "✅ Prerequisites check passed"
}

# Create deployment package
create_deployment_package() {
    local function_name=$1
    local lambda_file=$2
    
    echo "📦 Creating deployment package for $function_name..."
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    PACKAGE_DIR="$TEMP_DIR/$function_name"
    mkdir -p "$PACKAGE_DIR"
    
    # Copy source code
    cp -r src/ "$PACKAGE_DIR/"
    cp "lambda/$lambda_file" "$PACKAGE_DIR/lambda_function.py"
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -t "$PACKAGE_DIR"
    fi
    
    # Create ZIP package
    cd "$PACKAGE_DIR"
    zip -r "../${function_name}.zip" .
    cd - > /dev/null
    
    # Move package to build directory
    mkdir -p build
    mv "$TEMP_DIR/${function_name}.zip" "build/"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    echo "✅ Package created: build/${function_name}.zip"
}

# Deploy Lambda function
deploy_lambda_function() {
    local function_name=$1
    local description=$2
    local handler=$3
    
    echo "🚀 Deploying Lambda function: $function_name..."
    
    # Check if function exists
    if aws lambda get-function --function-name "$function_name" &> /dev/null; then
        echo "   Updating existing function..."
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file "fileb://build/${function_name}.zip"
        
        aws lambda update-function-configuration \
            --function-name "$function_name" \
            --runtime "$LAMBDA_RUNTIME" \
            --handler "$handler" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY"
    else
        echo "   Creating new function..."
        
        # Get IAM role ARN (create if doesn't exist)
        ROLE_NAME="sentinel-lambda-execution-role"
        ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null || echo "")
        
        if [ -z "$ROLE_ARN" ]; then
            echo "   Creating IAM role..."
            
            # Create trust policy
            cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
            
            # Create role
            aws iam create-role \
                --role-name "$ROLE_NAME" \
                --assume-role-policy-document file://trust-policy.json
            
            # Attach policies
            aws iam attach-role-policy \
                --role-name "$ROLE_NAME" \
                --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            
            aws iam attach-role-policy \
                --role-name "$ROLE_NAME" \
                --policy-arn "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
            
            aws iam attach-role-policy \
                --role-name "$ROLE_NAME" \
                --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
            
            # Wait for role to be available
            sleep 10
            
            ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
            rm trust-policy.json
        fi
        
        # Create function
        aws lambda create-function \
            --function-name "$function_name" \
            --runtime "$LAMBDA_RUNTIME" \
            --role "$ROLE_ARN" \
            --handler "$handler" \
            --zip-file "fileb://build/${function_name}.zip" \
            --description "$description" \
            --timeout "$LAMBDA_TIMEOUT" \
            --memory-size "$LAMBDA_MEMORY" \
            --environment Variables="{CRDB_CONNECTION_STRING=$CRDB_CONNECTION_STRING}"
    fi
    
    echo "✅ Function deployed: $function_name"
}

# Create API Gateway
create_api_gateway() {
    echo "🌐 Setting up API Gateway..."
    
    # Check if API exists
    API_ID=$(aws apigateway get-rest-apis --query "items[?name=='sentinel-dashboard-api'].id" --output text)
    
    if [ -z "$API_ID" ] || [ "$API_ID" == "None" ]; then
        echo "   Creating new API..."
        API_ID=$(aws apigateway create-rest-api \
            --name "sentinel-dashboard-api" \
            --description "Sentinel Dashboard API" \
            --query 'id' --output text)
        
        # Get root resource ID
        ROOT_RESOURCE_ID=$(aws apigateway get-resources \
            --rest-api-id "$API_ID" \
            --query 'items[?path==`/`].id' --output text)
        
        # Create resources and methods (simplified for demo)
        # In production, you'd create the full API structure here
        
        echo "   API created with ID: $API_ID"
    else
        echo "   Using existing API: $API_ID"
    fi
    
    echo "✅ API Gateway configured"
}

# Main deployment
main() {
    echo "🛡️  Sentinel Deployment"
    echo "======================"
    
    check_prerequisites
    
    # Load environment variables
    if [ -f ".env" ]; then
        source .env
        echo "✅ Environment variables loaded"
    else
        echo "⚠️  No .env file found. Using environment defaults."
    fi
    
    # Create deployment packages
    create_deployment_package "$EVENT_PROCESSOR_FUNCTION" "event_processor.py"
    create_deployment_package "$DASHBOARD_API_FUNCTION" "dashboard_api.py"
    
    # Deploy Lambda functions
    deploy_lambda_function "$EVENT_PROCESSOR_FUNCTION" "Sentinel Event Processor" "lambda_function.lambda_handler"
    deploy_lambda_function "$DASHBOARD_API_FUNCTION" "Sentinel Dashboard API" "lambda_function.lambda_handler"
    
    # Set up API Gateway
    create_api_gateway
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure your CockroachDB connection string"
    echo "2. Run 'python scripts/setup_database.py' to set up the schema"
    echo "3. Test the deployment with 'python scripts/demo_data_generator.py'"
    echo ""
    echo "Lambda Functions:"
    echo "- Event Processor: $EVENT_PROCESSOR_FUNCTION"
    echo "- Dashboard API: $DASHBOARD_API_FUNCTION"
    echo ""
}

# Run main function
main "$@"
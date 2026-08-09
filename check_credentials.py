"""
Credential checker for Sentinel - Verify your setup
"""
import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def print_header(title):
    print(f"\n{'='*50}")
    print(f"🔐 {title}")
    print('='*50)


def print_check(name, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")


async def check_aws_credentials():
    """Check AWS credentials and Bedrock access"""
    print_header("AWS CREDENTIALS CHECK")
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Check basic AWS credentials
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print_check("AWS Credentials", True, f"Account: {identity.get('Account', 'Unknown')}")
        except NoCredentialsError:
            print_check("AWS Credentials", False, "No credentials found. Run 'aws configure'")
            return False
        except Exception as e:
            print_check("AWS Credentials", False, f"Error: {e}")
            return False
        
        # Check Bedrock access
        try:
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            # Try to list models (this tests permissions)
            bedrock.list_foundation_models()
            print_check("Bedrock Access", True, "Can access Bedrock models")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'UnauthorizedOperation':
                print_check("Bedrock Access", False, "No Bedrock permissions. Check IAM policy")
            else:
                print_check("Bedrock Access", False, f"Error: {error_code}")
            return False
        except Exception as e:
            print_check("Bedrock Access", False, f"Error: {e}")
            return False
        
        # Test embedding generation
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
            from src.embedding_service import EmbeddingService
            
            service = EmbeddingService()
            if service.provider == "bedrock":
                test_embedding = await service.generate_embedding("test text")
                if len(test_embedding) == 1024 and any(x != 0 for x in test_embedding):
                    print_check("Bedrock Embeddings", True, "Successfully generated test embedding")
                else:
                    print_check("Bedrock Embeddings", False, "Invalid embedding returned")
            else:
                print_check("Bedrock Embeddings", False, f"Using fallback provider: {service.provider}")
                
        except Exception as e:
            print_check("Bedrock Embeddings", False, f"Error: {e}")
        
        return True
        
    except ImportError:
        print_check("boto3 Package", False, "Install with: pip install boto3")
        return False


async def check_openai_credentials():
    """Check OpenAI credentials"""
    print_header("OPENAI CREDENTIALS CHECK")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print_check("OpenAI API Key", False, "Set OPENAI_API_KEY environment variable")
        return False
    
    print_check("OpenAI API Key", True, f"Key found: {api_key[:8]}...")
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a small embedding request
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test",
            dimensions=1024
        )
        
        embedding = response.data[0].embedding
        print_check("OpenAI Embeddings", True, f"Generated {len(embedding)}D embedding")
        return True
        
    except ImportError:
        print_check("openai Package", False, "Install with: pip install openai")
        return False
    except Exception as e:
        print_check("OpenAI API", False, f"Error: {e}")
        return False


async def check_database():
    """Check database connection"""
    print_header("DATABASE CONNECTION CHECK")
    
    connection_string = os.getenv('CRDB_CONNECTION_STRING')
    if not connection_string:
        print_check("Connection String", False, "Set CRDB_CONNECTION_STRING environment variable")
        return False
    
    # Hide password in display
    display_string = connection_string
    if '@' in display_string:
        parts = display_string.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            user_pass[1] = '***'
            parts[0] = ':'.join(user_pass)
            display_string = '@'.join(parts)
    
    print_check("Connection String", True, f"Found: {display_string}")
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(connection_string)
        
        # Test basic query
        result = await conn.fetchval('SELECT version()')
        print_check("Database Connection", True, f"Connected to: {result[:50]}...")
        
        # Test vector extension if available
        try:
            await conn.execute('SELECT vector(ARRAY[1,2,3])')
            print_check("Vector Extension", True, "Vector operations available")
        except Exception:
            print_check("Vector Extension", False, "Vector extension not available (PostgreSQL)")
        
        await conn.close()
        return True
        
    except ImportError:
        print_check("asyncpg Package", False, "Install with: pip install asyncpg")
        return False
    except Exception as e:
        print_check("Database Connection", False, f"Error: {e}")
        return False


def check_local_dependencies():
    """Check local embedding dependencies"""
    print_header("LOCAL DEPENDENCIES CHECK")
    
    # Check sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='.cache')
        print_check("Sentence Transformers", True, "Model loaded successfully")
    except ImportError:
        print_check("Sentence Transformers", False, "Install with: pip install sentence-transformers")
    except Exception as e:
        print_check("Sentence Transformers", False, f"Error: {e}")
    
    # Check scikit-learn
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer()
        print_check("Scikit-learn", True, "TF-IDF vectorizer available")
    except ImportError:
        print_check("Scikit-learn", False, "Install with: pip install scikit-learn")
    except Exception as e:
        print_check("Scikit-learn", False, f"Error: {e}")


async def main():
    """Main credential checker"""
    print("🛡️ SENTINEL CREDENTIALS CHECKER")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🔍 Checking your Sentinel setup...\n")
    
    # Check all credential types
    aws_ok = await check_aws_credentials()
    openai_ok = await check_openai_credentials()
    db_ok = await check_database()
    check_local_dependencies()
    
    # Summary
    print_header("SETUP SUMMARY")
    
    if aws_ok:
        print("🚀 PRODUCTION READY: AWS Bedrock + CockroachDB")
        print("   Best performance and scalability")
    elif openai_ok and db_ok:
        print("🏗️ DEVELOPMENT READY: OpenAI + Database")
        print("   Good for development and testing")
    elif db_ok:
        print("💻 DATABASE READY: Local embeddings + Database")
        print("   Works for demos with real data persistence")
    else:
        print("🎭 DEMO READY: Local embeddings + Mock data")
        print("   Perfect for presentations and quick demos")
    
    print("\n📚 Next steps:")
    
    if not aws_ok and not openai_ok:
        print("   1. For better embeddings: Set up AWS or OpenAI credentials")
    
    if not db_ok:
        print("   2. For data persistence: Set up CockroachDB connection")
    
    print("   3. Start demo: python local_server.py")
    print("   4. Run tests: python test_sentinel.py")
    
    print("\n🔗 Setup guides:")
    print("   - Full setup: CREDENTIALS_SETUP.md")
    print("   - Quick start: README.md")
    print("   - Architecture: ARCHITECTURE.md")


if __name__ == "__main__":
    asyncio.run(main())
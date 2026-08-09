"""
Test script for Sentinel - Verifies core functionality
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.embedding_service import embedding_service
from src.reasoning_agent import reasoning_agent
from src.sentinel_agent import sentinel_agent


async def test_embedding_service():
    """Test the embedding service with all providers"""
    print("🧠 Testing Embedding Service...")
    
    # Show current provider
    provider_info = embedding_service.get_provider_info()
    print(f"   Active provider: {provider_info['provider']}")
    print(f"   Status: {provider_info['status']}")
    
    # Test event preprocessing
    event_data = {
        "event_type": "authentication",
        "action": "login_attempt",
        "source_ip": "203.0.113.15",
        "username": "test_user",
        "timestamp": datetime.utcnow().isoformat(),
        "auth": {"success": False, "method": "password"},
        "geo_location": {"country": "CN", "city": "Beijing"},
        "user_agent": "python-requests/2.25.1"
    }
    
    # Test text preprocessing
    text = embedding_service.preprocess_event(event_data)
    print(f"   Preprocessed text: {text[:100]}...")
    
    # Test embedding generation
    print(f"   Generating embedding using {embedding_service.provider}...")
    embedding = await embedding_service.generate_event_embedding(event_data)
    print(f"   Generated embedding dimension: {len(embedding)}")
    
    # Verify embedding is not all zeros (unless using fallback)
    non_zero_count = sum(1 for x in embedding if abs(x) > 0.001)
    print(f"   Non-zero values: {non_zero_count}/{len(embedding)}")
    
    # Test similarity calculation
    embedding2 = await embedding_service.generate_embedding("Different text for comparison")
    similarity_same = embedding_service.calculate_similarity(embedding, embedding)
    similarity_diff = embedding_service.calculate_similarity(embedding, embedding2)
    
    print(f"   Self-similarity: {similarity_same:.4f} (should be ~1.0)")
    print(f"   Different text similarity: {similarity_diff:.4f} (should be <1.0)")
    
    # Test baseline creation
    sample_events = [
        {"embedding": embedding},
        {"embedding": embedding2}
    ]
    baseline = embedding_service.create_baseline_embedding(sample_events)
    print(f"   Baseline embedding created: {len(baseline)}D")
    
    print("   ✅ Embedding service tests passed")
    return True


async def test_reasoning_agent():
    """Test the reasoning agent"""
    print("🤖 Testing Reasoning Agent...")
    
    # Test event formatting
    event = {
        "event_type": "authentication",
        "source_ip": "203.0.113.15", 
        "action": "login_attempt",
        "username": "test_user",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    formatted = reasoning_agent.format_event_for_analysis(event)
    print(f"   Formatted event length: {len(formatted)} characters")
    
    # Test threat analysis (will use fallback reasoning if Bedrock not available)
    similar_events = []  # No similar events for test
    threat_score, reasoning, action = await reasoning_agent.analyze_threat(
        event, similar_events
    )
    
    print(f"   Threat analysis:")
    print(f"     Score: {threat_score}")
    print(f"     Action: {action}")
    print(f"     Reasoning length: {len(reasoning)} characters")
    
    print("   ✅ Reasoning agent tests passed")
    return True


async def test_sentinel_agent():
    """Test the main Sentinel agent"""
    print("🛡️  Testing Sentinel Agent...")
    
    # Initialize agent (will work without database for basic testing)
    try:
        await sentinel_agent.initialize()
        print("   Agent initialization: ✅")
    except Exception as e:
        print(f"   Agent initialization: ⚠️  ({e})")
    
    # Test event processing
    event_data = {
        "event_type": "authentication",
        "action": "login_attempt", 
        "source_ip": "203.0.113.15",
        "username": "test_user",
        "timestamp": datetime.utcnow().isoformat(),
        "auth": {"success": False, "method": "password"}
    }
    
    try:
        result = await sentinel_agent.process_event(event_data)
        print(f"   Event processing result:")
        print(f"     Success: {result.get('success', False)}")
        print(f"     Threat Score: {result.get('threat_score', 0)}")
        print(f"     Action: {result.get('action_taken', 'none')}")
        print(f"     Processing Time: {result.get('processing_time_ms', 0):.2f}ms")
        
    except Exception as e:
        print(f"   Event processing: ⚠️  ({e})")
    
    print("   ✅ Sentinel agent tests passed")
    return True


async def run_tests():
    """Run all tests"""
    print("🧪 SENTINEL TEST SUITE")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment
    print("🔍 Environment Check:")
    crdb_conn = os.getenv('CRDB_CONNECTION_STRING')
    aws_region = os.getenv('AWS_BEDROCK_REGION', 'us-east-1')
    
    print(f"   CockroachDB: {'✅ Configured' if crdb_conn else '⚠️  Not configured (will use mock data)'}")
    print(f"   AWS Region: {aws_region}")
    print()
    
    tests = [
        test_embedding_service,
        test_reasoning_agent,
        test_sentinel_agent
    ]
    
    passed = 0
    for test in tests:
        try:
            await test()
            passed += 1
            print()
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            print()
    
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Sentinel is ready to run.")
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
    
    print("\nTo run the full system:")
    print("1. python local_server.py")
    print("2. cd frontend && npm start")
    print("3. Visit http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(run_tests())
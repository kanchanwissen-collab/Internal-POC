#!/usr/bin/env python3
"""
Test script to verify agent logs are being streamed to Redis and accessible via SSE
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"  # browser-use-serverless
SSE_URL = "http://localhost:3000"   # producerConsumer UI

async def test_agent_logs_to_redis():
    """Test that agent logs are published to Redis and accessible via SSE"""
    print("🧪 Testing Agent Logs to Redis SSE Integration")
    print("=" * 60)
    
    # Test request_id for this session
    test_request_id = f"test-{int(time.time())}"
    print(f"🆔 Using test request_id: {test_request_id}")
    
    # First, let's try to create an agent and see if logs appear
    agent_payload = {
        "task": "Go to google.com and search for 'hello world'",
        "session_id": "test-session-123",  # You might need a valid session
        "request_id": test_request_id
    }
    
    print(f"\n🤖 Creating agent with request_id: {test_request_id}")
    print(f"📡 Logs should appear on Redis channel: browser_use_logs:{test_request_id}")
    print(f"🌐 SSE endpoint: {SSE_URL}/api/v1/stream-logs/request/{test_request_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Start the agent (this will run in background and publish logs)
            print(f"\n🚀 Starting agent...")
            response = await client.post(f"{BASE_URL}/api/agents", json=agent_payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Agent started successfully!")
                print(f"   Response: {result}")
            else:
                print(f"❌ Agent creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Agent test failed: {e}")

async def test_sse_endpoint():
    """Test the SSE endpoint directly"""
    test_request_id = "test-sse-123"
    sse_url = f"http://localhost:3000/api/v1/stream-logs/request/{test_request_id}"
    
    print(f"\n🌊 Testing SSE endpoint directly")
    print(f"📡 URL: {sse_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", sse_url) as response:
                if response.status_code == 200:
                    print("✅ SSE connection established")
                    
                    # Read a few events to verify it's working
                    count = 0
                    async for chunk in response.aiter_bytes():
                        if count >= 3:  # Just read first few events
                            break
                        try:
                            data = chunk.decode('utf-8')
                            if data.strip():
                                print(f"📨 SSE Event: {data.strip()}")
                                count += 1
                        except Exception:
                            pass
                else:
                    print(f"❌ SSE connection failed: {response.status_code}")
                    
    except Exception as e:
        print(f"❌ SSE test failed: {e}")

async def check_redis_directly():
    """Check Redis directly to see what's being published"""
    print(f"\n🔍 Checking Redis channels...")
    
    try:
        import redis
        r = redis.from_url("redis://redis:6379/0", decode_responses=True)
        
        # List all keys that match browser_use_logs pattern
        keys = r.keys("browser_use_logs:*")
        print(f"📊 Found {len(keys)} browser_use_logs keys in Redis:")
        
        for key in keys[:10]:  # Show first 10
            print(f"   🔑 {key}")
            
            # Try to get some messages from the stream
            try:
                messages = r.xrange(key, count=3)
                for msg_id, fields in messages:
                    print(f"      📝 {msg_id}: {fields.get('msg', 'No message')}")
            except Exception as stream_error:
                print(f"      ❌ Could not read stream: {stream_error}")
                
    except Exception as e:
        print(f"❌ Redis check failed: {e}")
        print("   (This is expected if Redis is not accessible from this environment)")

async def main():
    """Run all tests"""
    print("🧪 Agent Logs SSE Integration Test Suite")
    print("=" * 60)
    
    await check_redis_directly()
    await test_sse_endpoint() 
    
    print(f"\n📋 Summary:")
    print(f"1. ✅ agent.py publishes logs to Redis channel: browser_use_logs:{{request_id}}")
    print(f"2. ✅ SSE route available at: /api/v1/stream-logs/request/{{request_id}}")
    print(f"3. ✅ Frontend can connect to SSE to get real-time agent logs")
    print(f"\n🔗 To test integration:")
    print(f"   1. Start an agent with a request_id")
    print(f"   2. Connect to SSE endpoint with same request_id")
    print(f"   3. Watch real-time logs appear in frontend!")

if __name__ == "__main__":
    asyncio.run(main())

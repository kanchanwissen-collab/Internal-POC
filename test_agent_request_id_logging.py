#!/usr/bin/env python3
"""
Test script to verify agent.py publishes logs using request_id only.
This script tests the Redis publishing mechanism and SSE integration.
"""

import os
import sys
import json
import time
import redis
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any

# Add the browser-use-serverless path for imports
sys.path.append(r'c:\Users\Admin\Documents\Internal-POC\browser-use-serverless')

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
AGENT_API_URL = "http://localhost:8000"  # Adjust based on your setup
SSE_API_URL = "http://localhost:3000"   # Adjust based on your UI setup

def test_redis_connection():
    """Test Redis connection and check existing streams."""
    print("🔍 Testing Redis connection...")
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        print("✅ Redis connection successful")
        
        # List all stream keys
        streams = r.keys("browser_use_logs:*")
        print(f"📊 Found {len(streams)} existing log streams:")
        for stream in streams[:10]:  # Show first 10
            count = r.xlen(stream)
            print(f"  - {stream}: {count} messages")
        
        return r
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return None

def test_stream_pattern(redis_client, request_id: str):
    """Test the stream naming pattern."""
    print(f"\n🧪 Testing stream pattern for request_id: {request_id}")
    
    expected_stream = f"browser_use_logs:{request_id}"
    print(f"📡 Expected stream name: {expected_stream}")
    
    # Check if stream exists
    exists = redis_client.exists(expected_stream)
    print(f"🔍 Stream exists: {exists}")
    
    if exists:
        length = redis_client.xlen(expected_stream)
        print(f"📊 Stream length: {length} messages")
        
        # Get last few messages
        messages = redis_client.xrevrange(expected_stream, count=5)
        print(f"📝 Last 5 messages:")
        for msg_id, fields in messages:
            print(f"  {msg_id}: {fields.get('msg', '')[:100]}...")
    
    return expected_stream

def monitor_redis_pubsub(redis_client, request_id: str, duration: int = 30):
    """Monitor Redis pub/sub for a specific request_id."""
    print(f"\n📻 Monitoring pub/sub for request_id: {request_id} (duration: {duration}s)")
    
    channel = f"browser_use_logs:{request_id}"
    pubsub = redis_client.pubsub()
    
    try:
        pubsub.subscribe(channel)
        print(f"🎧 Subscribed to channel: {channel}")
        
        start_time = time.time()
        message_count = 0
        
        for message in pubsub.listen():
            if time.time() - start_time > duration:
                break
                
            if message['type'] == 'message':
                message_count += 1
                data = message['data']
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(data)
                    print(f"📨 JSON Message {message_count}:")
                    print(f"   Agent: {parsed.get('agent_name', 'N/A')}")
                    print(f"   Request ID: {parsed.get('request_id', 'N/A')}")
                    print(f"   Message: {parsed.get('msg', data)[:100]}...")
                    print(f"   Timestamp: {parsed.get('timestamp', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"📨 Text Message {message_count}: {data[:100]}...")
        
        print(f"📊 Total messages received: {message_count}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
    finally:
        pubsub.unsubscribe(channel)
        pubsub.close()

async def test_sse_endpoint(request_id: str, duration: int = 30):
    """Test the SSE endpoint for real-time logs."""
    print(f"\n🌊 Testing SSE endpoint for request_id: {request_id}")
    
    sse_url = f"{SSE_API_URL}/api/v1/stream-logs/request/{request_id}"
    print(f"🔗 SSE URL: {sse_url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=duration + 5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(sse_url) as response:
                if response.status != 200:
                    print(f"❌ SSE endpoint returned status: {response.status}")
                    return
                
                print("✅ SSE connection established")
                start_time = time.time()
                event_count = 0
                
                async for line in response.content:
                    if time.time() - start_time > duration:
                        break
                        
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        event_count += 1
                        try:
                            data = json.loads(line[6:])  # Remove 'data: '
                            event_type = data.get('type', 'unknown')
                            
                            if event_type == 'log':
                                log_data = data.get('data', {})
                                print(f"📨 SSE Log Event {event_count}:")
                                print(f"   Request ID: {log_data.get('request_id', 'N/A')}")
                                print(f"   Source: {log_data.get('source', 'N/A')}")
                                print(f"   Message: {log_data.get('message', '')[:100]}...")
                            elif event_type == 'connected':
                                print(f"🔗 SSE Connected: {data.get('message', '')}")
                            elif event_type == 'heartbeat':
                                print("💓 SSE Heartbeat")
                            else:
                                print(f"📨 SSE Event {event_count} ({event_type}): {data}")
                        except json.JSONDecodeError:
                            print(f"📨 SSE Raw Event {event_count}: {line}")
                
                print(f"📊 Total SSE events received: {event_count}")
                
    except Exception as e:
        print(f"❌ SSE test failed: {e}")

def simulate_agent_request(redis_client, request_id: str):
    """Simulate what the agent does - publish test messages."""
    print(f"\n🤖 Simulating agent behavior for request_id: {request_id}")
    
    stream_key = f"browser_use_logs:{request_id}"
    
    test_messages = [
        "INFO 2025-09-21 10:00:00 [Agent] Starting agent task",
        "INFO 2025-09-21 10:00:01 [BrowserSession] Opening browser",
        "INFO 2025-09-21 10:00:02 [Agent] Processing step 1",
        "[Agent] print path check",
        "📍 Step 1: Navigate to website",
        "🦾 [ACTION] Click button",
        "📄 Result: Button clicked successfully",
    ]
    
    for i, msg in enumerate(test_messages):
        # 1. Add to stream
        redis_client.xadd(stream_key, {"msg": msg})
        
        # 2. Publish to pub/sub (JSON format)
        payload = json.dumps({
            "agent_name": "browser agent",
            "msg": msg,
            "request_id": request_id,
            "timestamp": time.time(),
            "source": "test_simulation"
        })
        redis_client.publish(stream_key, payload)
        
        print(f"📤 Published message {i+1}: {msg[:50]}...")
        time.sleep(1)  # Small delay between messages

async def main():
    """Main test function."""
    print("🧪 Agent Request ID Logging Test")
    print("=" * 50)
    
    # Test Redis connection
    r = test_redis_connection()
    if not r:
        return
    
    # Use a test request ID
    test_request_id = f"test_req_{int(time.time())}"
    print(f"\n🆔 Using test request_id: {test_request_id}")
    
    # Test stream pattern
    stream_name = test_stream_pattern(r, test_request_id)
    
    print("\n" + "="*50)
    print("Choose a test to run:")
    print("1. Monitor Redis pub/sub (30 seconds)")
    print("2. Test SSE endpoint (30 seconds)")
    print("3. Simulate agent messages and monitor")
    print("4. Check existing streams")
    print("5. Run all tests")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        monitor_redis_pubsub(r, test_request_id)
    elif choice == "2":
        await test_sse_endpoint(test_request_id)
    elif choice == "3":
        print("Starting simulation in 3 seconds... Start monitoring in another terminal!")
        time.sleep(3)
        simulate_agent_request(r, test_request_id)
    elif choice == "4":
        # List and inspect existing streams
        streams = r.keys("browser_use_logs:*")
        for stream in streams:
            print(f"\n🔍 Inspecting stream: {stream}")
            length = r.xlen(stream)
            print(f"📊 Messages: {length}")
            if length > 0:
                recent = r.xrevrange(stream, count=3)
                for msg_id, fields in recent:
                    print(f"  {msg_id}: {fields.get('msg', '')[:80]}...")
    elif choice == "5":
        print("🚀 Running all tests...")
        print("\n1. Simulating agent messages...")
        simulate_agent_request(r, test_request_id)
        
        print("\n2. Testing SSE endpoint...")
        await test_sse_endpoint(test_request_id, 15)
        
        print("\n3. Checking Redis streams...")
        test_stream_pattern(r, test_request_id)
        
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())

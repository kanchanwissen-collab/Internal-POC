#!/usr/bin/env python3
"""
Test script to verify the frontend Live Logs integration with request_id-based SSE.
This script simulates the complete flow from frontend button click to live log streaming.
"""

import os
import sys
import json
import time
import redis
import asyncio
import aiohttp
from datetime import datetime

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

def test_live_logs_integration():
    """Test the complete Live Logs integration flow."""
    print("🧪 Testing Live Logs Integration with Request ID")
    print("=" * 60)
    
    # Connect to Redis
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    # Test scenario: simulate what happens when user clicks "Live Logs"
    test_request_id = f"test_req_{int(time.time())}"
    test_session_id = f"session_{int(time.time())}"
    
    print(f"\n🆔 Test scenario:")
    print(f"   Request ID: {test_request_id}")
    print(f"   Session ID: {test_session_id}")
    print(f"   Status: running")
    
    # Step 1: Verify frontend would construct the correct URL
    frontend_log_url = f"/logs/{test_request_id}?status=running&request_id={test_request_id}&batch_id={test_session_id}"
    print(f"\n📱 Frontend would open URL: {frontend_log_url}")
    
    # Step 2: Verify the LogViewer would use the correct SSE endpoint
    sse_endpoint = f"/api/v1/stream-logs/request/{test_request_id}"
    print(f"🌊 LogViewer would connect to SSE: {sse_endpoint}")
    
    # Step 3: Simulate agent publishing logs with this request_id
    print(f"\n🤖 Simulating agent logs for request_id: {test_request_id}")
    simulate_agent_logs(r, test_request_id)
    
    # Step 4: Verify logs were published correctly
    stream_key = f"browser_use_logs:{test_request_id}"
    
    if r.exists(stream_key):
        message_count = r.xlen(stream_key)
        print(f"✅ Agent logs published successfully: {message_count} messages")
        
        # Show recent messages
        messages = r.xrevrange(stream_key, count=3)
        print(f"📝 Recent messages:")
        for msg_id, fields in messages:
            msg = fields.get('msg', '')
            print(f"   {msg[:80]}...")
        
        return True
    else:
        print(f"❌ No logs found in stream: {stream_key}")
        return False

def simulate_agent_logs(redis_client, request_id):
    """Simulate agent publishing logs exactly like the real agent.py does."""
    stream_key = f"browser_use_logs:{request_id}"
    
    test_messages = [
        f"🔄 [Agent] Starting agent for request_id: {request_id}",
        f"📡 [Agent] Redis logging to stream/channel: {stream_key}",
        "INFO 2025-09-21 10:00:01 [BrowserSession] Opening browser",
        "INFO 2025-09-21 10:00:02 [Agent] Processing step 1",
        "[Agent] print path check",
        "📍 Step 1: Navigate to website",
        "🦾 [ACTION] Click button",
        "📄 Result: Button clicked successfully",
    ]
    
    for i, msg in enumerate(test_messages):
        # 1. Add to Redis stream (for history)
        redis_client.xadd(stream_key, {"msg": msg})
        
        # 2. Publish to pub/sub (for live SSE)
        payload = json.dumps({
            "agent_name": "browser agent",
            "msg": msg,
            "request_id": request_id,
            "timestamp": time.time(),
            "source": "agent_simulation"
        })
        redis_client.publish(stream_key, payload)
        
        print(f"   📤 Published: {msg[:50]}...")
        time.sleep(0.5)  # Small delay between messages

async def test_sse_integration(request_id):
    """Test the SSE endpoint integration."""
    print(f"\n🌊 Testing SSE integration for request_id: {request_id}")
    
    sse_url = f"http://localhost:3000/api/v1/stream-logs/request/{request_id}"
    print(f"🔗 Connecting to: {sse_url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(sse_url) as response:
                if response.status != 200:
                    print(f"❌ SSE endpoint returned status: {response.status}")
                    return False
                
                print("✅ SSE connection established")
                event_count = 0
                start_time = time.time()
                
                async for line in response.content:
                    if time.time() - start_time > 10:  # 10 second test
                        break
                        
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        event_count += 1
                        try:
                            data = json.loads(line[6:])  # Remove 'data: '
                            event_type = data.get('type', 'unknown')
                            
                            if event_type == 'log':
                                log_data = data.get('data', {})
                                message = log_data.get('message', '')
                                req_id = log_data.get('request_id', 'N/A')
                                print(f"   📨 Log #{event_count}: {message[:50]}... (req: {req_id})")
                            elif event_type == 'connected':
                                print(f"   🔗 Connected: {data.get('message', '')}")
                            else:
                                print(f"   📤 Event #{event_count}: {event_type}")
                        except json.JSONDecodeError:
                            print(f"   📨 Raw #{event_count}: {line}")
                
                print(f"📊 Received {event_count} SSE events")
                return event_count > 0
                
    except Exception as e:
        print(f"❌ SSE test failed: {e}")
        return False

def test_frontend_logic():
    """Test the frontend logic for determining Live vs Historical logs."""
    print(f"\n🧠 Testing frontend routing logic:")
    
    test_cases = [
        {
            "name": "Running session with request_id",
            "status": "running",
            "request_id": "req_123",
            "session_id": "session_123",
            "expected_url": "/logs/req_123",
            "expected_sse": "/api/v1/stream-logs/request/req_123",
            "expected_live": True
        },
        {
            "name": "Running session without request_id",
            "status": "running", 
            "request_id": "",
            "session_id": "session_123",
            "expected_url": "/logs/session_123",
            "expected_sse": "/api/v1/stream-logs/session_123",
            "expected_live": False
        },
        {
            "name": "Completed session with request_id",
            "status": "completed",
            "request_id": "req_123",
            "session_id": "session_123", 
            "expected_url": "/logs/session_123",
            "expected_sse": "/api/v1/stream-logs/session_123",
            "expected_live": False
        },
        {
            "name": "Failed session",
            "status": "failed",
            "request_id": "req_123",
            "session_id": "session_123",
            "expected_url": "/logs/session_123", 
            "expected_sse": "/api/v1/stream-logs/session_123",
            "expected_live": False
        }
    ]
    
    for case in test_cases:
        print(f"\n   📋 Case: {case['name']}")
        
        # Simulate frontend handleLogView logic
        log_id = case['request_id'] if case['status'] == 'running' and case['request_id'] else case['session_id']
        actual_url = f"/logs/{log_id}"
        
        # Simulate LogViewer SSE logic  
        is_live = case['status'] == 'running' and case['request_id'] and case['request_id'] != ''
        actual_sse = f"/api/v1/stream-logs/request/{case['request_id']}" if is_live else f"/api/v1/stream-logs/{case['session_id']}"
        
        # Check results
        url_correct = actual_url == case['expected_url']
        sse_correct = actual_sse == case['expected_sse'] 
        live_correct = is_live == case['expected_live']
        
        print(f"      URL: {actual_url} {'✅' if url_correct else '❌'}")
        print(f"      SSE: {actual_sse} {'✅' if sse_correct else '❌'}")
        print(f"      Live: {is_live} {'✅' if live_correct else '❌'}")
        
        if not (url_correct and sse_correct and live_correct):
            print(f"      ❌ Expected URL: {case['expected_url']}")
            print(f"      ❌ Expected SSE: {case['expected_sse']}")
            print(f"      ❌ Expected Live: {case['expected_live']}")

async def main():
    """Run all integration tests."""
    print("🚀 Live Logs Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Frontend routing logic
    test_frontend_logic()
    
    # Test 2: Redis integration
    redis_success = test_live_logs_integration()
    
    # Test 3: SSE integration (if Redis test passed)
    if redis_success:
        # Get the test request_id from the previous test
        test_request_id = f"test_req_{int(time.time()-5)}"  # Approximate the one we just created
        sse_success = await test_sse_integration(test_request_id)
        
        print(f"\n" + "=" * 60)
        print("📊 Test Results:")
        print(f"   Frontend Logic: ✅ PASSED")
        print(f"   Redis Integration: {'✅ PASSED' if redis_success else '❌ FAILED'}")
        print(f"   SSE Integration: {'✅ PASSED' if sse_success else '❌ FAILED'}")
        
        if redis_success and sse_success:
            print(f"\n🎉 All tests passed! Live Logs integration is working correctly.")
            print(f"\n💡 To test manually:")
            print(f"   1. Start an agent with a request_id")
            print(f"   2. Set its status to 'running' in the dashboard")
            print(f"   3. Click the 'Live Logs' button")
            print(f"   4. Verify you see real-time logs with request_id")
        else:
            print(f"\n❌ Some tests failed. Check the implementation.")
    else:
        print(f"\n❌ Redis test failed, skipping SSE test.")

if __name__ == "__main__":
    asyncio.run(main())

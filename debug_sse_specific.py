#!/usr/bin/env python3
"""
Test the SSE endpoint specifically for the working session.
Since we confirmed Redis pub/sub is working, let's test the SSE connection.
"""

import subprocess
import time
import threading
import requests
from datetime import datetime

def test_sse_connection():
    """Test the SSE endpoint for the known working session."""
    request_id = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
    sse_url = f"http://localhost:3000/api/v1/stream-logs/request/{request_id}"
    
    print("🧪 Testing SSE Connection for Active Session")
    print("=" * 60)
    print(f"Request ID: {request_id}")
    print(f"SSE URL: {sse_url}")
    
    # Test 1: Basic HTTP connectivity
    print("\n1. Testing basic HTTP connectivity...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        print(f"   ✅ UI server responding (status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ UI server not accessible: {e}")
        return False
    
    # Test 2: Test SSE endpoint with curl
    print("\n2. Testing SSE endpoint with curl...")
    try:
        print(f"   🔗 Connecting to: {sse_url}")
        
        # Use subprocess to run curl for SSE
        curl_cmd = [
            "curl", "-N", "-s", 
            "-H", "Accept: text/event-stream",
            "-H", "Cache-Control: no-cache",
            "-m", "15",  # 15 second timeout
            sse_url
        ]
        
        print("   ⏱️ Listening for 15 seconds...")
        
        process = subprocess.Popen(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        event_count = 0
        start_time = time.time()
        
        # Read output line by line
        for line in process.stdout:
            line = line.strip()
            if line:
                event_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"   [{timestamp}] Event #{event_count}: {line[:100]}...")
                
                # Stop after getting some events or timeout
                if event_count >= 10 or (time.time() - start_time) > 15:
                    process.terminate()
                    break
        
        # Get any errors
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"   ⚠️ Curl stderr: {stderr_output}")
        
        print(f"   📊 Total events received: {event_count}")
        
        if event_count > 0:
            print("   ✅ SSE endpoint is working!")
            return True
        else:
            print("   ❌ No SSE events received")
            return False
            
    except Exception as e:
        print(f"   ❌ SSE test failed: {e}")
        return False

def test_ui_redis_connection():
    """Test if the UI can connect to Redis directly."""
    print("\n3. Testing UI Redis connection...")
    
    try:
        # Check if we can access Redis from the UI container
        # This is a bit tricky without being inside the container
        print("   💡 To test UI Redis connection manually:")
        print("   docker exec ui-container-name redis-cli -h redis ping")
        print("   or check UI container logs for Redis connection errors")
        
        # We can test from our current environment
        import redis
        r = redis.from_url("redis://redis:6379/0", decode_responses=True)
        r.ping()
        print("   ✅ Redis accessible from current environment")
        
        # Check the specific stream
        stream_key = "browser_use_logs:597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
        if r.exists(stream_key):
            length = r.xlen(stream_key)
            print(f"   ✅ Stream exists: {stream_key} ({length} messages)")
        else:
            print(f"   ❌ Stream not found: {stream_key}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Redis connection test failed: {e}")
        return False

def suggest_fixes():
    """Provide specific fix suggestions."""
    print("\n" + "=" * 60)
    print("🔧 Troubleshooting Suggestions:")
    
    print("\n1. Check UI container logs for SSE/Redis errors:")
    print("   docker logs ui-container-name | grep -i redis")
    print("   docker logs ui-container-name | grep -i sse")
    
    print("\n2. Check Redis URL in UI environment:")
    print("   docker exec ui-container-name env | grep REDIS")
    
    print("\n3. Test Redis from UI container:")
    print("   docker exec ui-container-name redis-cli -h redis ping")
    
    print("\n4. Check CORS and headers:")
    print("   - Verify SSE endpoint returns correct headers")
    print("   - Check browser Network tab for CORS errors")
    
    print("\n5. Restart UI service:")
    print("   docker-compose restart ui-service-name")
    
    print("\n6. Check Next.js API route configuration:")
    print("   - Verify route.ts file is correctly placed")
    print("   - Check for TypeScript compilation errors")

def main():
    """Run the comprehensive SSE test."""
    print("🚨 SSE Connection Debug (Redis is Working)")
    print("=" * 60)
    
    # Since we know Redis pub/sub works, focus on SSE
    sse_working = test_sse_connection()
    redis_working = test_ui_redis_connection()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Redis Pub/Sub: ✅ CONFIRMED WORKING (from your test)")
    print(f"   SSE Endpoint: {'✅ WORKING' if sse_working else '❌ NOT WORKING'}")
    print(f"   Redis Access: {'✅ WORKING' if redis_working else '❌ NOT WORKING'}")
    
    if not sse_working:
        suggest_fixes()
        
        print("\n🎯 Most Likely Issues:")
        print("1. UI container using different Redis URL/instance")
        print("2. SSE endpoint Redis connection configuration")
        print("3. CORS or HTTP connection issues")
        print("4. Next.js API route not properly deployed/compiled")
        
    else:
        print("\n🎉 SSE is working! The frontend issue might be:")
        print("1. Browser CORS restrictions")
        print("2. Frontend JavaScript errors")
        print("3. EventSource implementation issues")

if __name__ == "__main__":
    main()

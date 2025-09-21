#!/usr/bin/env python3
"""
Test the new request_id SSE endpoint on the API server.
"""

import requests
import time
import json

def test_api_server_sse():
    """Test the SSE endpoint on the API server (port 8000)."""
    request_id = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
    
    # Test different possible endpoints
    endpoints_to_test = [
        f"http://localhost:8000/api/v1/stream-logs/request/{request_id}",
        f"http://34.60.81.78:8000/api/v1/stream-logs/request/{request_id}",
    ]
    
    print("🧪 Testing API Server SSE Endpoints")
    print("=" * 60)
    print(f"Request ID: {request_id}")
    
    for i, sse_url in enumerate(endpoints_to_test):
        print(f"\n{i+1}. Testing: {sse_url}")
        
        try:
            # First test basic connectivity
            base_url = sse_url.split('/api')[0]
            print(f"   Testing base connectivity: {base_url}")
            
            try:
                response = requests.get(f"{base_url}/docs", timeout=5)
                print(f"   ✅ API server responding (status: {response.status_code})")
            except Exception as e:
                print(f"   ❌ API server not accessible: {e}")
                continue
            
            # Test the SSE endpoint
            print(f"   🌊 Testing SSE endpoint...")
            
            response = requests.get(sse_url, headers={
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }, timeout=15, stream=True)
            
            print(f"   📊 Response status: {response.status_code}")
            print(f"   📋 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"   ✅ SSE endpoint is accessible!")
                print(f"   📻 Reading SSE stream (15 seconds)...")
                
                event_count = 0
                start_time = time.time()
                
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        event_count += 1
                        print(f"   Event #{event_count}: {line[:100]}...")
                        
                        # Parse data if it's a data line
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                event_type = data.get('type', 'unknown')
                                message = data.get('message', '')
                                print(f"      Type: {event_type}")
                                if message:
                                    print(f"      Message: {message[:80]}...")
                            except:
                                pass
                    
                    # Stop after some time or events
                    if (time.time() - start_time) > 15 or event_count > 20:
                        break
                
                print(f"   📊 Total events received: {event_count}")
                
                if event_count > 0:
                    print(f"   🎉 SSE endpoint is working!")
                    return True
                else:
                    print(f"   ⚠️ SSE connected but no events received")
                    
            else:
                error_text = response.text[:200] if hasattr(response, 'text') else 'No error details'
                print(f"   ❌ SSE endpoint error: {error_text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection error: {e}")
        except requests.exceptions.Timeout as e:
            print(f"   ❌ Timeout error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
    
    return False

def test_redis_from_api_server():
    """Test Redis connectivity from our environment (similar to API server)."""
    print(f"\n🔍 Testing Redis connectivity...")
    
    try:
        import redis
        
        # Test with the same Redis configuration as the API server
        redis_configs = [
            {"host": "redis", "port": 6379},      # Docker internal
            {"host": "localhost", "port": 6379},  # Local
        ]
        
        for config in redis_configs:
            try:
                r = redis.Redis(**config, decode_responses=True)
                r.ping()
                print(f"   ✅ Redis accessible at {config['host']}:{config['port']}")
                
                # Check the specific stream
                stream_key = "browser_use_logs:597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
                if r.exists(stream_key):
                    length = r.xlen(stream_key)
                    print(f"   ✅ Stream exists: {stream_key} ({length} messages)")
                    
                    # Test pub/sub
                    print(f"   🧪 Testing pub/sub subscription...")
                    pubsub = r.pubsub()
                    pubsub.subscribe(stream_key)
                    print(f"   ✅ Successfully subscribed to {stream_key}")
                    pubsub.close()
                    
                    return True
                else:
                    print(f"   ⚠️ Stream not found: {stream_key}")
                    all_streams = r.keys("browser_use_logs:*")
                    print(f"   📊 Found {len(all_streams)} agent streams total")
                    
            except Exception as e:
                print(f"   ❌ Redis connection failed ({config['host']}): {e}")
                
    except ImportError:
        print(f"   ❌ Redis library not available")
    except Exception as e:
        print(f"   ❌ Redis test failed: {e}")
    
    return False

def main():
    """Run all tests."""
    print("🚨 API Server SSE Debug")
    print("=" * 60)
    
    # Test Redis first
    redis_working = test_redis_from_api_server()
    
    # Test SSE endpoints
    sse_working = test_api_server_sse()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Redis Connection: {'✅ WORKING' if redis_working else '❌ FAILED'}")
    print(f"   SSE Endpoint: {'✅ WORKING' if sse_working else '❌ FAILED'}")
    
    if not sse_working:
        print("\n🔧 Troubleshooting steps:")
        print("1. Restart the API server:")
        print("   docker-compose restart api_server")
        print("")
        print("2. Check API server logs:")
        print("   docker logs api-server")
        print("")
        print("3. Verify the new SSE endpoint is available:")
        print("   curl http://localhost:8000/docs")
        print("   (Look for /api/v1/stream-logs/request/{request_id})")
        print("")
        print("4. Test Redis from API server container:")
        print("   docker exec api-server python -c \"import redis; r=redis.Redis(host='redis'); print(r.ping())\"")

if __name__ == "__main__":
    main()

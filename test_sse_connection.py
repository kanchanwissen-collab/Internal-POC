#!/usr/bin/env python3
"""
Test script to check the SSE endpoint directly for the session from the screenshot.
"""

import asyncio
import aiohttp
import json

async def test_sse_endpoint():
    """Test the SSE endpoint for the specific session."""
    request_id = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
    sse_url = f"http://localhost:3000/api/v1/stream-logs/request/{request_id}"
    
    print(f"🧪 Testing SSE endpoint: {sse_url}")
    print("=" * 60)
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print("🔗 Connecting to SSE endpoint...")
            
            async with session.get(sse_url, headers={
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }) as response:
                
                print(f"📊 Response status: {response.status}")
                print(f"📋 Response headers: {dict(response.headers)}")
                
                if response.status != 200:
                    body = await response.text()
                    print(f"❌ Error response body: {body}")
                    return False
                
                print("✅ SSE connection established")
                print("📻 Listening for events (30 seconds)...")
                
                event_count = 0
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        event_count += 1
                        try:
                            data = json.loads(line[6:])  # Remove 'data: '
                            event_type = data.get('type', 'unknown')
                            message = data.get('message', '')
                            timestamp = data.get('timestamp', '')
                            
                            print(f"📨 Event #{event_count}: {event_type}")
                            print(f"   Message: {message}")
                            print(f"   Time: {timestamp}")
                            
                            if event_type == 'log':
                                log_data = data.get('data', {})
                                print(f"   Log: {log_data.get('message', 'N/A')}")
                                print(f"   Source: {log_data.get('source', 'N/A')}")
                            
                        except json.JSONDecodeError:
                            print(f"📨 Raw event #{event_count}: {line}")
                
                print(f"\n📊 Total events received: {event_count}")
                return event_count > 0
                
    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Possible causes:")
        print("   - UI server not running on localhost:3000")
        print("   - SSE endpoint not accessible")
        print("   - Network/firewall issues")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_ui_server():
    """Test if the UI server is running."""
    print("🔍 Checking if UI server is accessible...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:3000", timeout=5) as response:
                print(f"✅ UI server is running (status: {response.status})")
                return True
    except Exception as e:
        print(f"❌ UI server not accessible: {e}")
        print("💡 Start the UI server with: npm run dev")
        return False

async def main():
    """Run all tests."""
    print("🚨 Debugging Live Logs Connection Error")
    print("=" * 60)
    
    # Test 1: Check if UI server is running
    ui_running = await test_ui_server()
    
    if not ui_running:
        print("\n❌ Cannot test SSE endpoint - UI server not running")
        return
    
    # Test 2: Test the specific SSE endpoint
    print("\n" + "=" * 60)
    sse_working = await test_sse_endpoint()
    
    print("\n" + "=" * 60)
    print("🔧 Troubleshooting Results:")
    print(f"   UI Server: {'✅ Running' if ui_running else '❌ Not accessible'}")
    print(f"   SSE Endpoint: {'✅ Working' if sse_working else '❌ Connection failed'}")
    
    if not sse_working:
        print("\n💡 Next steps:")
        print("1. Check UI server logs for errors")
        print("2. Verify Redis is running and accessible")
        print("3. Check if the request_id has an active agent")
        print("4. Test Redis connectivity from the UI container")

if __name__ == "__main__":
    asyncio.run(main())

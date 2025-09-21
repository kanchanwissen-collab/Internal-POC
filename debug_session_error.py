#!/usr/bin/env python3
"""
Quick debug script to check what's happening with the specific session from the screenshot.
"""

import redis
import json
import time

def debug_specific_session():
    """Debug the specific session from the screenshot."""
    print("🔍 Debugging Live Logs Connection Error")
    print("=" * 50)
    
    # Session details from screenshot
    session_id = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
    request_id = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"  # Same as session_id
    
    print(f"Session ID: {session_id}")
    print(f"Request ID: {request_id}")
    print(f"Status: running")
    
    # Connect to Redis
    try:
        r = redis.from_url("redis://redis:6379/0", decode_responses=True)
        r.ping()
        print("\n✅ Redis connection successful")
    except Exception as e:
        print(f"\n❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running: docker-compose up -d redis")
        return
    
    # Check the expected stream
    stream_key = f"browser_use_logs:{request_id}"
    print(f"\n🔍 Checking stream: {stream_key}")
    
    if r.exists(stream_key):
        length = r.xlen(stream_key)
        print(f"✅ Stream exists with {length} messages")
        
        # Show recent messages
        if length > 0:
            messages = r.xrevrange(stream_key, count=5)
            print(f"\n📝 Recent messages:")
            for i, (msg_id, fields) in enumerate(messages):
                msg = fields.get('msg', '')
                print(f"  {i+1}. {msg}")
        else:
            print("📝 Stream exists but has no messages")
    else:
        print("❌ Stream does not exist")
        
        # Check if there are any streams at all
        all_streams = r.keys("browser_use_logs:*")
        print(f"\n🔍 All agent streams ({len(all_streams)}):")
        for stream in all_streams[:10]:  # Show first 10
            length = r.xlen(stream)
            print(f"  - {stream}: {length} messages")
    
    # Check pub/sub activity
    print(f"\n📻 Testing pub/sub for channel: {stream_key}")
    pubsub = r.pubsub()
    
    try:
        pubsub.subscribe(stream_key)
        print(f"🎧 Subscribed to {stream_key}")
        print("⏰ Waiting 10 seconds for messages...")
        
        message_count = 0
        start_time = time.time()
        
        for message in pubsub.listen():
            if time.time() - start_time > 10:
                break
                
            if message['type'] == 'message':
                message_count += 1
                data = message['data']
                print(f"📨 Message {message_count}: {data[:100]}...")
        
        if message_count == 0:
            print("❌ No pub/sub messages received")
            print("💡 This means the agent is not actively publishing logs")
        else:
            print(f"✅ Received {message_count} pub/sub messages")
            
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped")
    finally:
        pubsub.unsubscribe(stream_key)
        pubsub.close()
    
    # Check if there's an agent running for this session
    print(f"\n🤖 Checking for active agent...")
    
    # Look for any recent activity in Redis
    recent_streams = []
    for stream in r.keys("browser_use_logs:*"):
        try:
            # Get the latest message timestamp
            latest = r.xrevrange(stream, count=1)
            if latest:
                msg_id = latest[0][0]
                timestamp = int(msg_id.split('-')[0])
                age_minutes = (time.time() * 1000 - timestamp) / (1000 * 60)
                if age_minutes < 30:  # Active in last 30 minutes
                    recent_streams.append((stream, age_minutes))
        except:
            pass
    
    if recent_streams:
        print(f"✅ Found {len(recent_streams)} recently active streams:")
        for stream, age in sorted(recent_streams, key=lambda x: x[1]):
            print(f"  - {stream}: {age:.1f} minutes ago")
    else:
        print("❌ No recently active agent streams found")
    
    # Provide troubleshooting suggestions
    print(f"\n🔧 Troubleshooting suggestions:")
    print(f"1. Check if the agent is actually running for request_id: {request_id}")
    print(f"2. Verify the SSE endpoint is accessible:")
    print(f"   curl -N 'http://localhost:3000/api/v1/stream-logs/request/{request_id}'")
    print(f"3. Check browser network tab for SSE connection errors")
    print(f"4. Verify Redis is accessible from both agent and UI containers")
    print(f"5. Check agent logs to see if it's publishing to Redis")

if __name__ == "__main__":
    debug_specific_session()

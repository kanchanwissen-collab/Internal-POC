#!/usr/bin/env python3
"""
Simple Redis monitor to watch agent log streams in real-time.
Use this while running agents to see live logging.
"""

import redis
import json
import time
import sys
from datetime import datetime

def monitor_all_agent_streams():
    """Monitor all agent log streams."""
    print("🔍 Starting Redis Stream Monitor for Agent Logs")
    print("=" * 60)
    
    try:
        r = redis.from_url("redis://redis:6379/0", decode_responses=True)
        r.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # Find all agent log streams
    streams = r.keys("browser_use_logs:*")
    print(f"📊 Found {len(streams)} agent log streams:")
    
    if not streams:
        print("❌ No agent log streams found. Start an agent first.")
        return
    
    for stream in streams:
        length = r.xlen(stream)
        print(f"  - {stream}: {length} messages")
    
    print("\n" + "="*60)
    print("Choose monitoring option:")
    print("1. Monitor all streams (pub/sub)")
    print("2. Read recent messages from all streams")
    print("3. Monitor specific request_id")
    print("4. Watch for new streams")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        monitor_pubsub_all(r, streams)
    elif choice == "2":
        read_recent_messages(r, streams)
    elif choice == "3":
        request_id = input("Enter request_id to monitor: ").strip()
        monitor_specific_request(r, request_id)
    elif choice == "4":
        watch_new_streams(r)

def monitor_pubsub_all(r, streams):
    """Monitor pub/sub for all agent streams."""
    print("\n📻 Monitoring pub/sub for all agent streams...")
    print("Press Ctrl+C to stop")
    
    pubsub = r.pubsub()
    
    # Subscribe to all stream channels
    for stream in streams:
        pubsub.subscribe(stream)
        print(f"🎧 Subscribed to: {stream}")
    
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel']
                data = message['data']
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Extract request_id from channel
                request_id = channel.split(':')[-1] if ':' in channel else 'unknown'
                
                try:
                    # Try parsing as JSON
                    parsed = json.loads(data)
                    print(f"\n[{timestamp}] 📨 {request_id}")
                    print(f"  Agent: {parsed.get('agent_name', 'N/A')}")
                    print(f"  Message: {parsed.get('msg', '')}")
                    if 'source' in parsed:
                        print(f"  Source: {parsed['source']}")
                except json.JSONDecodeError:
                    # Plain text message
                    print(f"\n[{timestamp}] 📨 {request_id}: {data}")
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped")
    finally:
        pubsub.close()

def read_recent_messages(r, streams):
    """Read recent messages from all streams."""
    print("\n📖 Reading recent messages from all streams...")
    
    for stream in streams:
        request_id = stream.split(':')[-1] if ':' in stream else 'unknown'
        print(f"\n🔍 Stream: {stream} (request_id: {request_id})")
        
        # Get last 5 messages
        messages = r.xrevrange(stream, count=5)
        if messages:
            for msg_id, fields in messages:
                msg = fields.get('msg', '')
                timestamp = msg_id.split('-')[0]
                dt = datetime.fromtimestamp(int(timestamp)/1000)
                print(f"  [{dt.strftime('%H:%M:%S')}] {msg}")
        else:
            print("  (no messages)")

def monitor_specific_request(r, request_id):
    """Monitor a specific request_id."""
    print(f"\n🎯 Monitoring request_id: {request_id}")
    
    channel = f"browser_use_logs:{request_id}"
    stream = channel
    
    # Check if stream exists
    if not r.exists(stream):
        print(f"❌ Stream {stream} does not exist")
        return
    
    print(f"✅ Stream exists with {r.xlen(stream)} messages")
    
    # Show recent messages
    print("\n📖 Recent messages:")
    messages = r.xrevrange(stream, count=10)
    for msg_id, fields in messages:
        msg = fields.get('msg', '')
        print(f"  {msg}")
    
    # Monitor live
    print(f"\n📻 Monitoring live updates on {channel}...")
    print("Press Ctrl+C to stop")
    
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = message['data']
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                try:
                    parsed = json.loads(data)
                    print(f"[{timestamp}] {parsed.get('msg', data)}")
                except json.JSONDecodeError:
                    print(f"[{timestamp}] {data}")
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped")
    finally:
        pubsub.close()

def watch_new_streams(r):
    """Watch for new agent streams being created."""
    print("\n👀 Watching for new agent streams...")
    print("Press Ctrl+C to stop")
    
    known_streams = set(r.keys("browser_use_logs:*"))
    print(f"📊 Currently tracking {len(known_streams)} streams")
    
    try:
        while True:
            current_streams = set(r.keys("browser_use_logs:*"))
            new_streams = current_streams - known_streams
            
            for new_stream in new_streams:
                request_id = new_stream.split(':')[-1] if ':' in new_stream else 'unknown'
                print(f"\n🆕 New stream detected: {new_stream}")
                print(f"   Request ID: {request_id}")
                
                # Show first few messages
                messages = r.xrange(new_stream, count=3)
                for msg_id, fields in messages:
                    msg = fields.get('msg', '')
                    print(f"   {msg[:80]}...")
            
            known_streams = current_streams
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n⏹️ Watch stopped")

if __name__ == "__main__":
    monitor_all_agent_streams()

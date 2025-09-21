#!/usr/bin/env python3
"""
Test script to simulate agent publishing logs and test SSE connectivity
"""
import redis
import json
import time
import threading

def publish_test_logs(request_id: str, duration: int = 30):
    """Publish test log messages to Redis channel like agent.py does"""
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Test Redis connection
        r.ping()
        print(f"✓ Connected to Redis")
        
        # Use the same pattern as agent.py
        channel = f"browser_use_logs:{request_id}"
        
        print(f"Publishing test logs to channel: {channel}")
        
        for i in range(duration):
            # Simulate agent.py log format
            log_data = {
                "msg": f"Test log message {i+1} - Agent is working...",
                "agent_name": "test-browser-agent", 
                "request_id": request_id,
                "timestamp": time.time(),
                "source": "test_script",
                "level": "INFO"
            }
            
            # Publish JSON log (PUBSUB_JSON=1 format)
            r.publish(channel, json.dumps(log_data))
            print(f"Published log {i+1}: {log_data['msg']}")
            
            time.sleep(2)  # Wait 2 seconds between messages
            
        print(f"✓ Finished publishing {duration} test messages")
        
    except Exception as e:
        print(f"✗ Error publishing logs: {e}")

if __name__ == "__main__":
    test_request_id = "67887c8a-7d12-47ff-b12c-9f13e9a11de8"
    print(f"Starting test log publisher for request_id: {test_request_id}")
    print("This will simulate an active agent publishing logs...")
    
    # Start publishing in background thread so we can test SSE concurrently
    publisher_thread = threading.Thread(target=publish_test_logs, args=(test_request_id, 15))
    publisher_thread.daemon = True
    publisher_thread.start()
    
    print("Test logs will be published for 30 seconds.")
    print("Now test the SSE endpoint with:")
    print(f"curl -H 'Accept: text/event-stream' http://localhost:8000/api/v1/stream-logs/request/{test_request_id}")
    
    # Keep main thread alive
    publisher_thread.join()

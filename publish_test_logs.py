import subprocess
import json
import time

def publish_test_log(request_id, message):
    """Publish a test log message to Redis channel"""
    channel = f"browser_use_logs:{request_id}"
    
    # Create a JSON log message
    log_data = {
        "msg": message,
        "agent_name": "test-browser-agent",
        "request_id": request_id,
        "timestamp": time.time(),
        "source": "test_script",
        "level": "INFO"
    }
    
    # Use docker exec to publish to Redis
    cmd = [
        "docker", "exec", "redis", "redis-cli", 
        "PUBLISH", channel, json.dumps(log_data)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ Published to {channel}: {message}")
            return True
        else:
            print(f"✗ Failed to publish: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error publishing: {e}")
        return False

if __name__ == "__main__":
    request_id = "67887c8a-7d12-47ff-b12c-9f13e9a11de8"
    
    print(f"Publishing test logs for request_id: {request_id}")
    
    messages = [
        "🚀 Agent starting up...",
        "📋 Loading browser automation tasks",
        "🌐 Opening browser session", 
        "🔍 Analyzing page content",
        "✅ Task completed successfully",
        "📊 Generating report"
    ]
    
    for i, message in enumerate(messages):
        if publish_test_log(request_id, f"Step {i+1}: {message}"):
            print(f"Published message {i+1}")
        time.sleep(2)
    
    print("✓ Finished publishing test messages")
    print("Check the SSE test page to see if messages appear!")

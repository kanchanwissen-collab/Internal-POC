import requests
import time
import json

# Test the SSE endpoint
request_id = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
sse_url = f"http://localhost:3000/api/v1/stream-logs/request/{request_id}"

print(f"Testing SSE endpoint: {sse_url}")

try:
    # First test basic connectivity
    print("1. Testing basic UI server connectivity...")
    response = requests.get("http://localhost:3000", timeout=5)
    print(f"   Status: {response.status_code}")
    
    # Test the SSE endpoint
    print("2. Testing SSE endpoint...")
    response = requests.get(sse_url, headers={
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache"
    }, timeout=10, stream=True)
    
    print(f"   SSE Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("3. Reading SSE stream...")
        for i, line in enumerate(response.iter_lines(decode_unicode=True)):
            if line:
                print(f"   Event {i}: {line}")
            if i > 10:  # Stop after 10 events
                break
    else:
        print(f"   Error: {response.text}")
        
except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
    print("UI server may not be running on localhost:3000")
except Exception as e:
    print(f"Error: {e}")

print("Done")

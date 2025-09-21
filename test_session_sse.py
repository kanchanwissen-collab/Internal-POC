#!/usr/bin/env python3
"""
Test script to verify SSE endpoint connectivity for session ID: 67887c8a-7d12-47ff-b12c-9f13e9a11de8
"""
import requests
import time
import sys

def test_sse_endpoint():
    session_id = "67887c8a-7d12-47ff-b12c-9f13e9a11de8"
    
    # Test the API server health first
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✓ API Server Health: {health_response.status_code} - {health_response.text}")
    except Exception as e:
        print(f"✗ API Server Health Check Failed: {e}")
        return False

    # Test the SSE endpoint
    sse_url = f"http://localhost:8000/api/v1/stream-logs/request/{session_id}"
    print(f"Testing SSE endpoint: {sse_url}")
    
    try:
        response = requests.get(
            sse_url, 
            stream=True, 
            timeout=10,
            headers={
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
        )
        
        print(f"✓ SSE Response Status: {response.status_code}")
        print(f"✓ SSE Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✓ SSE Connection established successfully!")
            print("Listening for events (10 seconds)...")
            
            start_time = time.time()
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"Received: {line}")
                if time.time() - start_time > 10:
                    print("Timeout reached, closing connection")
                    break
        else:
            print(f"✗ SSE Connection failed with status: {response.status_code}")
            print(f"Response body: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ SSE Connection timeout")
        return False
    except Exception as e:
        print(f"✗ SSE Connection error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing SSE endpoint for session: 67887c8a-7d12-47ff-b12c-9f13e9a11de8")
    success = test_sse_endpoint()
    sys.exit(0 if success else 1)

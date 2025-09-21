#!/usr/bin/env python3
"""
Test script to verify batch_id is included in dashboard API response
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"

async def test_batch_id_inclusion():
    """Test that the dashboard API returns actual batch_id for requests"""
    print("🔍 Testing batch_id inclusion in dashboard API...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test dashboard requests
            response = await client.get(f"{BASE_URL}/api/dashboard/requests?limit=20")
            
            if response.status_code != 200:
                print(f"❌ API call failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
                
            requests_data = response.json()
            print(f"✅ Got {len(requests_data)} requests")
            
            # Check for batch_id field
            requests_with_batch_id = 0
            requests_without_batch_id = 0
            unique_batch_ids = set()
            unique_request_ids = set()
            
            for req in requests_data:
                request_id = req.get("request_id", "N/A")
                batch_id = req.get("batch_id")
                
                unique_request_ids.add(request_id)
                
                if batch_id and batch_id != "Unknown" and batch_id != request_id:
                    requests_with_batch_id += 1
                    unique_batch_ids.add(batch_id)
                    print(f"   Request {request_id[:8]}... → Batch {batch_id[:8]}...")
                else:
                    requests_without_batch_id += 1
                    print(f"   Request {request_id[:8]}... → No batch_id (value: {batch_id})")
            
            print(f"\n📊 Summary:")
            print(f"   Total requests: {len(requests_data)}")
            print(f"   Requests with actual batch_id: {requests_with_batch_id}")
            print(f"   Requests without batch_id: {requests_without_batch_id}")
            print(f"   Unique request_ids: {len(unique_request_ids)}")
            print(f"   Unique batch_ids: {len(unique_batch_ids)}")
            
            if unique_batch_ids:
                print(f"   Batch IDs found: {sorted(list(unique_batch_ids))}")
            
            # Check if request_id != batch_id for any requests
            different_ids = []
            for req in requests_data:
                request_id = req.get("request_id")
                batch_id = req.get("batch_id")
                if batch_id and batch_id != request_id and batch_id != "Unknown":
                    different_ids.append((request_id, batch_id))
            
            if different_ids:
                print(f"✅ Found {len(different_ids)} requests where batch_id differs from request_id")
                print("   This means actual batch_ids are being returned!")
            else:
                print("⚠️  All batch_ids are same as request_ids or Unknown - may need to check data")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

async def test_producerConsumer_api():
    """Test the producerConsumer API as well to compare"""
    print("\n🔍 Testing producerConsumer API for batch_id...")
    
    PRODUCER_URL = "http://localhost:8000"  # Assuming producerConsumer runs on 8000
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PRODUCER_URL}/api/v1/prior-auths/requests")
            
            if response.status_code != 200:
                print(f"❌ ProducerConsumer API call failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return
                
            result = response.json()
            requests_data = result.get("data", [])
            print(f"✅ Got {len(requests_data)} requests from producerConsumer")
            
            # Check for batch_id field
            for req in requests_data[:5]:  # Show first 5
                request_id = req.get("request_id", "N/A")
                batch_id = req.get("batch_id", "N/A")
                print(f"   Request {request_id[:8]}... → Batch {batch_id}")
                
        except Exception as e:
            print(f"❌ ProducerConsumer test failed: {e}")

async def main():
    """Run all tests"""
    print("🧪 Testing Batch ID Inclusion in APIs")
    print("=" * 50)
    
    await test_batch_id_inclusion()
    await test_producerConsumer_api()
    
    print("\n✅ Batch ID tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

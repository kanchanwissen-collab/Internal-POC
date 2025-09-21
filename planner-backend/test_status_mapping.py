#!/usr/bin/env python3
"""
Test script to verify status mapping for dashboard API
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"

async def test_status_mapping():
    """Test that the dashboard API returns frontend-friendly statuses"""
    print("🔍 Testing status mapping in dashboard API...")
    
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
            
            # Check status values
            statuses_found = set()
            batch_ids_found = set()
            for req in requests_data:
                status = req.get("status")
                batch_id = req.get("batch_id")
                statuses_found.add(status)
                if batch_id:
                    batch_ids_found.add(batch_id)
                print(f"   Request {req['request_id'][:8]}... - Status: {status}, Batch: {batch_id}")
            
            print(f"\n📊 Status values found: {sorted(statuses_found)}")
            print(f"📊 Batch IDs found: {len(batch_ids_found)} unique batch IDs")
            
            # Verify we're getting frontend statuses
            expected_statuses = {"running", "failed", "queued", "manual-action", "completed"}
            frontend_statuses = statuses_found.intersection(expected_statuses)
            db_statuses = statuses_found - expected_statuses
            
            if frontend_statuses:
                print(f"✅ Frontend statuses found: {sorted(frontend_statuses)}")
            if db_statuses:
                print(f"⚠️  Raw DB statuses still present: {sorted(db_statuses)}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

async def test_dashboard_stats():
    """Test dashboard stats with status mapping"""
    print("\n📈 Testing dashboard stats...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/dashboard/stats")
            
            if response.status_code != 200:
                print(f"❌ Stats API call failed: {response.status_code}")
                return
                
            stats = response.json()
            print(f"✅ Dashboard stats:")
            print(f"   Total requests: {stats['total_requests']}")
            print(f"   Pending (running/queued): {stats['pending_requests']}")
            print(f"   Completed: {stats['completed_requests']}")
            print(f"   Failed: {stats['failed_requests']}")
            print(f"   Manual action required: {stats['user_action_required']}")
            print(f"   Success rate: {stats['success_rate']}%")
                
        except Exception as e:
            print(f"❌ Stats test failed: {e}")

async def main():
    """Run all tests"""
    print("🧪 Testing Status Mapping for Dashboard API")
    print("=" * 50)
    
    await test_status_mapping()
    await test_dashboard_stats()
    
    print("\n✅ Status mapping tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

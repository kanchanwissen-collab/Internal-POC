# Batch ID Implementation Summary

## Problem
The frontend was showing the same value for both `request_id` and `batch_id` because the API wasn't returning the actual `batch_id` from the database.

## Solution
Updated both backend APIs and the frontend to properly handle and display actual `batch_id` values from the database.

## Changes Made

### 1. producerConsumer/app/services/mongodb_service.py
- **Line 269**: Added `batch_id` field to the `get_all_request_progress_for_dashboard()` response
- **Line 269**: `"batch_id": request_details.get("batch_id", "Unknown") if request_details else "Unknown"`

### 2. planner-backend/api/dashboard_api.py
- **Line 37**: Added `batch_id: Optional[str] = None` to `RequestSummary` model
- **Lines 151-165**: Added logic to extract `batch_id` from multiple sources:
  1. From `priorAuthRequest.batchId` (if available)
  2. From `batch_requests.batch_id` (primary source)
  3. Additional fallback lookup if needed
- **Line 178**: Added `batch_id=batch_id` to `RequestSummary` creation

### 3. Frontend: ui-latest/src/app/(protected)/history/page.tsx
- **Line 11**: Added `batch_id: string | null;` to `DashboardApiItem` interface
- **Line 135**: Updated `sessionId` to use actual batch_id: `sessionId: req.batch_id || req.request_id`
- **Line 148**: Updated `batch_id` field: `batch_id: req.batch_id || "Unknown"`

## Data Flow
1. **Database**: `batch_requests` collection contains the actual `batch_id` for each `request_id`
2. **Backend APIs**: Both services now query `batch_requests` to get the actual `batch_id`
3. **Frontend**: Displays the actual `batch_id` instead of using `request_id` as fallback

## API Response Changes
Before:
```json
{
  "request_id": "597e433d-f3f9-4cd9-ba71-4c2b8deef68b",
  "patient_name": "Unknown",
  "status": "running"
}
```

After:
```json
{
  "request_id": "597e433d-f3f9-4cd9-ba71-4c2b8deef68b", 
  "batch_id": "e115eba0-fda6-4d62-9c37-5c0f31ddda98",
  "patient_name": "Unknown", 
  "status": "running"
}
```

## Testing
Use the test script to verify batch_id inclusion:
```bash
cd c:\Users\Admin\Documents\Internal-POC\planner-backend
python test_batch_id.py
```

## Expected Result
- Frontend will now show different values for `request_id` and `batch_id`
- Multiple requests can share the same `batch_id` (grouped processing)
- Each `request_id` is unique but may belong to the same batch
- If no batch_id is found, it shows "Unknown" instead of duplicating request_id

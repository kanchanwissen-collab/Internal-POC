# Live Logs Integration with Request ID

## Overview

The Live Logs feature in the frontend dashboard has been updated to use `request_id`-based logging instead of `batch_id`. This enables real-time log streaming from agents directly to the frontend using Server-Sent Events (SSE).

## Implementation Details

### 🔄 Updated Components

#### 1. History Page (`history/page.tsx`)
- **Updated `handleLogView` function** to pass `request_id` and `batch_id` in query parameters
- **Smart routing logic**: Uses `request_id` for running sessions, falls back to `sessionId` for historical logs
- **Live Logs button** remains enabled only for `status === 'running'`

#### 2. Log Viewer (`logs/[sessionId]/page.tsx`)
- **Dual SSE endpoint support**:
  - Live logs: `/api/v1/stream-logs/request/{request_id}` (for running sessions)
  - Historical logs: `/api/v1/stream-logs/{sessionId}` (for completed sessions)
- **Enhanced UI**: Shows "LIVE" indicator with pulsing animation for real-time logs
- **Structured log parsing**: Handles JSON messages from agent with proper formatting
- **Automatic endpoint selection** based on session status and presence of request_id

#### 3. Agent Logging (`agents.py`)
- **Already correctly implemented** to use `request_id` only
- **Redis publishing pattern**: `browser_use_logs:{request_id}`
- **JSON payload format** includes `request_id`, `agent_name`, `msg`, and `timestamp`

#### 4. SSE Route (`stream-logs/request/[request_id]/route.ts`)
- **Request-based streaming** for real-time agent logs
- **JSON message parsing** with fallback to plain text
- **Heartbeat support** and error handling
- **Auto-reconnection** on connection failures

## 🚀 How It Works

### Frontend Flow

1. **User clicks "Live Logs"** on a running session
2. **History page** constructs URL with `request_id`: `/logs/{request_id}?status=running&request_id={request_id}`
3. **Log viewer** detects running status + request_id and connects to SSE endpoint
4. **Real-time streaming** begins from agent to frontend

### Backend Flow

1. **Agent starts** with `request_id` parameter
2. **Agent publishes logs** to Redis channel `browser_use_logs:{request_id}`
3. **SSE endpoint** subscribes to the same Redis channel
4. **Live logs stream** to any connected frontend clients

### Routing Logic

```typescript
// Frontend routing logic
const logId = sessionItem.status === 'running' && sessionItem.request_id 
    ? sessionItem.request_id  // Use request_id for live logs
    : sessionItem.sessionId;  // Use sessionId for historical logs

// SSE endpoint selection
const sseUrl = isLiveSession 
    ? `/api/v1/stream-logs/request/${requestId}`  // Real-time
    : `/api/v1/stream-logs/${sessionId}`;         // Historical
```

## 🧪 Testing

### Automated Tests

Run the comprehensive test suite:
```bash
python test_live_logs_integration.py
```

### Manual Testing

1. **Start the frontend application**
2. **Create an agent request** with a valid `request_id`
3. **Set session status to 'running'** in the dashboard
4. **Click "Live Logs"** button
5. **Verify real-time logs appear** with "LIVE" indicator

### Test Scripts Available

- `test_live_logs_integration.py` - Complete integration test
- `test_agent_request_id_logging.py` - Agent logging verification  
- `redis_monitor.py` - Real-time Redis monitoring
- `sse_test.html` - Browser-based SSE testing

## 📊 Key Features

### ✅ What Works

- **Real-time log streaming** from agents to frontend
- **Automatic endpoint selection** based on session status
- **Structured log messages** with source, timestamp, and request_id
- **Visual "LIVE" indicator** for active streaming sessions
- **Backward compatibility** with historical log viewing
- **Error handling** and auto-reconnection for SSE
- **Request_id validation** and fallback mechanisms

### 🎯 Status-Based Behavior

| Session Status | Button Text | Endpoint | Behavior |
|---------------|-------------|----------|----------|
| `running` | "Live Logs" | `/stream-logs/request/{request_id}` | Real-time streaming |
| `completed` | "Logs" | `/stream-logs/{sessionId}` | Historical logs |
| `failed` | "Logs" | `/stream-logs/{sessionId}` | Historical logs |
| `queued` | "Logs" (disabled) | N/A | Button disabled |

## 🔧 Configuration

### Environment Variables

- `REDIS_URL` - Redis connection string (default: `redis://redis:6379/0`)
- `NEXT_PUBLIC_API_URL` - API base URL for SSE endpoints

### Redis Channel Pattern

- **Live logs**: `browser_use_logs:{request_id}`
- **Historical logs**: `browser_use_logs:{batch_id}` (legacy)

## 🚨 Important Notes

1. **Request ID is required** for live log streaming to work
2. **Agent must publish** to the correct Redis channel pattern
3. **SSE endpoint must be accessible** from the frontend
4. **Browser compatibility** - SSE is supported in all modern browsers
5. **Connection management** - SSE connections are automatically cleaned up

## 🔄 Migration Notes

### From Batch ID to Request ID

The system now supports both approaches:
- **New implementation**: Uses `request_id` for live streaming
- **Legacy support**: Falls back to `batch_id` for historical logs
- **Automatic detection**: Frontend chooses the right approach based on session state

### No Breaking Changes

- Existing historical log viewing continues to work
- Legacy SSE endpoints remain functional
- Gradual migration path for existing sessions

## 🎉 Benefits

1. **Real-time visibility** into agent execution
2. **Better debugging** with live log streaming
3. **Improved user experience** with instant feedback
4. **Scalable architecture** using Redis pub/sub
5. **Flexible implementation** supporting both live and historical logs

## 🔍 Troubleshooting

### Common Issues

1. **No live logs appearing**:
   - Verify agent is using correct `request_id`
   - Check Redis connection and channels
   - Confirm SSE endpoint is accessible

2. **"Logs" button disabled**:
   - Session status must be 'running' for live logs
   - Check that `request_id` is present in session data

3. **SSE connection errors**:
   - Verify CORS settings for SSE endpoints
   - Check network connectivity to API server
   - Review browser console for error messages

### Debug Commands

```bash
# Check Redis streams
docker exec redis-container redis-cli KEYS "browser_use_logs:*"

# Monitor Redis pub/sub
docker exec redis-container redis-cli MONITOR

# Test SSE endpoint directly
curl -N "http://localhost:3000/api/v1/stream-logs/request/test_req_123"
```

This implementation provides a robust, scalable solution for real-time agent log streaming while maintaining backward compatibility with existing systems.

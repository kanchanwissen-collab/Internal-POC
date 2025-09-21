# Agent Logs SSE Integration

## Overview
This implementation enables real-time streaming of agent logs from `browser-use-serverless/app/routers/agents.py` to the frontend dashboard via Server-Sent Events (SSE) using Redis as the message broker.

## Architecture

```
[Agent.py] → [Redis Pub/Sub] → [SSE Endpoint] → [Frontend Dashboard]
```

### Data Flow
1. **Agent Execution**: When an agent runs, it publishes logs to Redis
2. **Redis Channel**: Uses pattern `browser_use_logs:{request_id}`
3. **SSE Streaming**: Frontend connects to SSE endpoint with request_id
4. **Real-time Updates**: Logs appear in dashboard as agent executes

## Implementation Details

### 1. Agent.py Redis Publishing

**File**: `browser-use-serverless/app/routers/agents.py`

**Key Changes**:
- Made `request_id` required (not optional)
- Enhanced Redis logging with request_id metadata
- Added startup logging for debugging
- Improved JSON payload structure

**Redis Channels**:
- **Pattern**: `browser_use_logs:{request_id}`
- **Example**: `browser_use_logs:597e433d-f3f9-4cd9-ba71-4c2b8deef68b`

**Log Message Format**:
```json
{
  "agent_name": "browser agent",
  "msg": "📍 Step 1: Navigate to google.com",
  "request_id": "597e433d-f3f9-4cd9-ba71-4c2b8deef68b",
  "timestamp": 1695307200.123,
  "source": "logger"
}
```

### 2. SSE Endpoint

**File**: `producerConsumer/ui-latest/src/app/api/v1/stream-logs/request/[request_id]/route.ts`

**Features**:
- Real-time log streaming via SSE
- Automatic Redis subscription/unsubscription
- Heartbeat for connection health
- Error handling and reconnection support
- JSON and plain text message support

**Endpoint**: `GET /api/v1/stream-logs/request/{request_id}`

**SSE Event Format**:
```json
{
  "type": "log",
  "data": {
    "level": "INFO",
    "message": "📍 Step 1: Navigate to google.com",
    "source": "browser-agent", 
    "request_id": "597e433d-f3f9-4cd9-ba71-4c2b8deef68b",
    "timestamp": "2025-09-21T10:30:00.000Z",
    "log_source": "logger"
  },
  "timestamp": "2025-09-21T10:30:00.000Z",
  "channel": "browser_use_logs:597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
}
```

## Usage Examples

### 1. Start Agent with Logging
```bash
curl -X POST http://localhost:8000/api/agents \\
  -H "Content-Type: application/json" \\
  -d '{
    "task": "Go to google.com and search for hello world",
    "session_id": "test-session-123",
    "request_id": "my-test-request-123"
  }'
```

### 2. Connect to SSE for Real-time Logs
```javascript
const eventSource = new EventSource('/api/v1/stream-logs/request/my-test-request-123');

eventSource.onmessage = (event) => {
  const logData = JSON.parse(event.data);
  if (logData.type === 'log') {
    console.log('Agent Log:', logData.data.message);
  }
};

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
};
```

### 3. Frontend Dashboard Integration
```typescript
// In your React component
useEffect(() => {
  if (!requestId) return;
  
  const eventSource = new EventSource(`/api/v1/stream-logs/request/${requestId}`);
  
  eventSource.onmessage = (event) => {
    const logData = JSON.parse(event.data);
    if (logData.type === 'log') {
      setLogs(prev => [...prev, logData.data]);
    }
  };
  
  return () => eventSource.close();
}, [requestId]);
```

## Configuration

### Environment Variables

**browser-use-serverless**:
```bash
REDIS_URL=redis://redis:6379/0
REDIS_STREAM=browser_use_logs
LOG_PUBSUB=1              # Enable pub/sub (required for SSE)
LOG_PUBSUB_JSON=1         # Use JSON format (recommended)
REDIS_STREAM_MAXLEN=1000  # Optional: limit stream length
```

**producerConsumer**:
```bash
REDIS_URL=redis://redis:6379
```

## Testing

### 1. Manual Testing
```bash
# Run the test script
python test_agent_sse_integration.py
```

### 2. Check Redis Directly
```bash
# Connect to Redis CLI
redis-cli

# List agent log streams
KEYS browser_use_logs:*

# Read latest messages from a stream
XRANGE browser_use_logs:your-request-id - + COUNT 10
```

### 3. Test SSE Connection
```bash
# Use curl to test SSE endpoint
curl -N -H "Accept: text/event-stream" \\
  http://localhost:3000/api/v1/stream-logs/request/your-request-id
```

## Benefits

1. **Real-time Monitoring**: See agent progress in real-time
2. **Request-specific Logs**: Each request has isolated log stream
3. **Scalable**: Redis pub/sub handles multiple concurrent agents
4. **Persistent History**: Redis streams provide log history
5. **Frontend Integration**: Easy to integrate with React/Next.js dashboards

## Troubleshooting

### Common Issues

1. **No logs appearing**:
   - Check if Redis is running
   - Verify `LOG_PUBSUB=1` in agent environment
   - Ensure request_id matches between agent and SSE endpoint

2. **SSE connection fails**:
   - Check if Redis is accessible from UI container
   - Verify REDIS_URL environment variable
   - Check browser network tab for connection errors

3. **Logs appear delayed**:
   - Check Redis network latency
   - Verify `LOG_PUBSUB=1` (pub/sub is faster than streams)
   - Check if browser is throttling SSE connections

### Debug Commands
```bash
# Check Redis connectivity
redis-cli ping

# Monitor Redis pub/sub activity
redis-cli monitor

# Check active Redis channels
redis-cli pubsub channels browser_use_logs:*
```

## Future Enhancements

1. **Log Filtering**: Add log level filtering (INFO, DEBUG, ERROR)
2. **Batch Logs**: Support streaming logs for entire batches
3. **Log Persistence**: Store logs in database for historical analysis
4. **Authentication**: Add authentication to SSE endpoints
5. **Rate Limiting**: Implement rate limiting for SSE connections

#!/bin/bash
# Simple bash script to test agent request_id logging

echo "🧪 Agent Request ID Logging - Quick Tests"
echo "========================================"

# Configuration
AGENT_API="http://localhost:8000"
UI_API="http://localhost:3000"
REQUEST_ID="test_req_$(date +%s)"

echo "🆔 Using test request_id: $REQUEST_ID"

echo ""
echo "📋 Available Tests:"
echo "1. Create test agent request"
echo "2. Test SSE endpoint"
echo "3. Check Redis directly"
echo "4. Monitor Redis logs"
echo "5. Full test sequence"

read -p "Choose test (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🤖 Creating test agent request..."
        curl -X POST "$AGENT_API/agents" \
             -H "Content-Type: application/json" \
             -d "{
                 \"task\": \"Test agent logging with request_id\",
                 \"session_id\": \"test_session_123\",
                 \"request_id\": \"$REQUEST_ID\"
             }" \
             -v
        ;;
    2)
        echo ""
        echo "🌊 Testing SSE endpoint..."
        echo "URL: $UI_API/api/v1/stream-logs/request/$REQUEST_ID"
        timeout 30 curl -N "$UI_API/api/v1/stream-logs/request/$REQUEST_ID" \
                        -H "Accept: text/event-stream" \
                        -H "Cache-Control: no-cache"
        ;;
    3)
        echo ""
        echo "📊 Checking Redis directly..."
        if command -v docker &> /dev/null; then
            echo "Using Docker to check Redis..."
            docker exec redis-container redis-cli KEYS "browser_use_logs:*" 2>/dev/null || \
            docker exec redis redis-cli KEYS "browser_use_logs:*" 2>/dev/null || \
            echo "❌ Could not find Redis container"
        elif command -v redis-cli &> /dev/null; then
            echo "Using local redis-cli..."
            redis-cli KEYS "browser_use_logs:*"
        else
            echo "❌ Neither Docker nor redis-cli found"
        fi
        ;;
    4)
        echo ""
        echo "📻 Monitoring Redis logs..."
        echo "This will monitor for 30 seconds. Start an agent in another terminal."
        if command -v docker &> /dev/null; then
            timeout 30 docker exec redis-container redis-cli MONITOR 2>/dev/null || \
            timeout 30 docker exec redis redis-cli MONITOR 2>/dev/null || \
            echo "❌ Could not find Redis container"
        else
            echo "❌ Docker not available for Redis monitoring"
        fi
        ;;
    5)
        echo ""
        echo "🚀 Running full test sequence..."
        
        echo "1. Checking Redis..."
        if command -v docker &> /dev/null; then
            docker exec redis-container redis-cli KEYS "browser_use_logs:*" 2>/dev/null || \
            docker exec redis redis-cli KEYS "browser_use_logs:*" 2>/dev/null
        fi
        
        echo ""
        echo "2. Testing SSE endpoint (10 seconds)..."
        timeout 10 curl -s "$UI_API/api/v1/stream-logs/request/$REQUEST_ID" \
                        -H "Accept: text/event-stream" &
        SSE_PID=$!
        
        sleep 2
        
        echo ""
        echo "3. Creating agent request..."
        curl -X POST "$AGENT_API/agents" \
             -H "Content-Type: application/json" \
             -d "{
                 \"task\": \"Test logging\",
                 \"session_id\": \"test_session\",
                 \"request_id\": \"$REQUEST_ID\"
             }" &
        AGENT_PID=$!
        
        echo ""
        echo "4. Waiting for test to complete..."
        sleep 15
        
        # Clean up background processes
        kill $SSE_PID 2>/dev/null || true
        
        echo ""
        echo "5. Checking final Redis state..."
        if command -v docker &> /dev/null; then
            echo "Stream for our request_id:"
            docker exec redis-container redis-cli XLEN "browser_use_logs:$REQUEST_ID" 2>/dev/null || \
            docker exec redis redis-cli XLEN "browser_use_logs:$REQUEST_ID" 2>/dev/null
            
            echo "Recent messages:"
            docker exec redis-container redis-cli XREVRANGE "browser_use_logs:$REQUEST_ID" + - COUNT 5 2>/dev/null || \
            docker exec redis redis-cli XREVRANGE "browser_use_logs:$REQUEST_ID" + - COUNT 5 2>/dev/null
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Test completed!"
echo ""
echo "💡 To see live logs, run in separate terminals:"
echo "   Terminal 1: python redis_monitor.py"
echo "   Terminal 2: Create agent request"
echo "   Terminal 3: curl $UI_API/api/v1/stream-logs/request/YOUR_REQUEST_ID"

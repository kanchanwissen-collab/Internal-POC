# PowerShell script to debug the Live Logs connection error

Write-Host "🚨 Debugging Live Logs Connection Error" -ForegroundColor Red
Write-Host "=" * 50

# Session details from the screenshot
$requestId = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"
$sessionId = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"

Write-Host "📋 Session Details:" -ForegroundColor Cyan
Write-Host "   Request ID: $requestId"
Write-Host "   Session ID: $sessionId"
Write-Host "   Status: running"

Write-Host "`n🔍 Running diagnostics..." -ForegroundColor Yellow

# Test 1: Check if UI server is running
Write-Host "`n1. Testing UI Server..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "   ✅ UI server is running (Status: $($response.StatusCode))" -ForegroundColor Green
    $uiRunning = $true
} catch {
    Write-Host "   ❌ UI server not accessible: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 Start with: npm run dev or docker-compose up ui" -ForegroundColor Yellow
    $uiRunning = $false
}

# Test 2: Check if SSE endpoint exists
if ($uiRunning) {
    Write-Host "`n2. Testing SSE Endpoint..." -ForegroundColor Cyan
    $sseUrl = "http://localhost:3000/api/v1/stream-logs/request/$requestId"
    Write-Host "   🔗 URL: $sseUrl"
    
    try {
        # Use curl for SSE testing (PowerShell Invoke-WebRequest doesn't handle SSE well)
        Write-Host "   🧪 Testing with curl..." -ForegroundColor Yellow
        $curlOutput = & cmd /c "curl -s -m 10 -H `"Accept: text/event-stream`" `"$sseUrl`""
        
        if ($LASTEXITCODE -eq 0 -and $curlOutput) {
            Write-Host "   ✅ SSE endpoint responded" -ForegroundColor Green
            Write-Host "   📝 Response preview:" -ForegroundColor Gray
            $curlOutput | Select-Object -First 5 | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
        } else {
            Write-Host "   ❌ SSE endpoint not responding" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ SSE test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 3: Check Redis connectivity
Write-Host "`n3. Testing Redis..." -ForegroundColor Cyan
try {
    # Check if Redis container is running
    $redisContainer = docker ps --filter "name=redis" --format "{{.Names}}" | Select-Object -First 1
    if ($redisContainer) {
        Write-Host "   ✅ Redis container found: $redisContainer" -ForegroundColor Green
        
        # Test Redis connectivity
        $redisTest = docker exec $redisContainer redis-cli ping 2>$null
        if ($redisTest -eq "PONG") {
            Write-Host "   ✅ Redis is responding" -ForegroundColor Green
            
            # Check for the specific stream
            $streamKey = "browser_use_logs:$requestId"
            $streamExists = docker exec $redisContainer redis-cli EXISTS $streamKey 2>$null
            if ($streamExists -eq "1") {
                $messageCount = docker exec $redisContainer redis-cli XLEN $streamKey 2>$null
                Write-Host "   ✅ Stream exists: $streamKey ($messageCount messages)" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️ Stream does not exist: $streamKey" -ForegroundColor Yellow
                Write-Host "   💡 This means no agent is publishing logs for this request_id" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ❌ Redis not responding" -ForegroundColor Red
        }
    } else {
        Write-Host "   ❌ Redis container not found" -ForegroundColor Red
        Write-Host "   💡 Start with: docker-compose up -d redis" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Redis test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check for active agents
Write-Host "`n4. Checking for Active Agents..." -ForegroundColor Cyan
try {
    # Check all browser-use streams
    if ($redisContainer) {
        $allStreams = docker exec $redisContainer redis-cli KEYS "browser_use_logs:*" 2>$null
        if ($allStreams) {
            $streamCount = ($allStreams | Measure-Object -Line).Lines
            Write-Host "   📊 Found $streamCount agent streams total" -ForegroundColor Green
            
            # Show recent streams
            Write-Host "   📝 Recent agent streams:" -ForegroundColor Gray
            $allStreams | Select-Object -First 5 | ForEach-Object {
                $length = docker exec $redisContainer redis-cli XLEN $_ 2>$null
                Write-Host "      $($_): $length messages" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ❌ No agent streams found" -ForegroundColor Red
            Write-Host "   💡 No agents have published logs yet" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ Agent check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Check if agent is running for this specific request
Write-Host "`n5. Checking Specific Agent..." -ForegroundColor Cyan
Write-Host "   🔍 Looking for agent with request_id: $requestId" -ForegroundColor Gray

# Check browser-use container
try {
    $agentContainer = docker ps --filter "name=browser-use" --format "{{.Names}}" | Select-Object -First 1
    if ($agentContainer) {
        Write-Host "   ✅ Browser-use container found: $agentContainer" -ForegroundColor Green
        
        # Check recent logs for this request_id
        $recentLogs = docker logs --tail 50 $agentContainer 2>$null | Select-String $requestId
        if ($recentLogs) {
            Write-Host "   ✅ Found logs mentioning request_id: $requestId" -ForegroundColor Green
            Write-Host "   📝 Recent log entries:" -ForegroundColor Gray
            $recentLogs | Select-Object -First 3 | ForEach-Object {
                Write-Host "      $($_.Line)" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ⚠️ No recent logs found for request_id: $requestId" -ForegroundColor Yellow
            Write-Host "   💡 Agent might not be running for this request" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ Browser-use container not found" -ForegroundColor Red
        Write-Host "   💡 Start with: docker-compose up -d browser-use-serverless" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Agent container check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary and recommendations
Write-Host "`n" + "=" * 50
Write-Host "🔧 Troubleshooting Summary:" -ForegroundColor Cyan

Write-Host "`n📋 Most likely causes of 'Connection error - retrying...':" -ForegroundColor Yellow
Write-Host "1. 🤖 No agent is actively running for request_id: $requestId"
Write-Host "2. 📡 Agent is not publishing logs to Redis (check agent logs)"
Write-Host "3. 🔌 Redis connection issues between UI and Redis"
Write-Host "4. 🌐 SSE endpoint not properly configured or accessible"

Write-Host "`n🚀 Recommended actions:" -ForegroundColor Green
Write-Host "1. Verify an agent is actually running for this session:"
Write-Host "   - Check if the session was properly started"
Write-Host "   - Look for agent startup logs"
Write-Host ""
Write-Host "2. Test Redis connectivity manually:"
Write-Host "   python debug_session_error.py"
Write-Host ""
Write-Host "3. Check UI server logs for SSE errors:"
Write-Host "   docker logs ui-container-name"
Write-Host ""
Write-Host "4. Test SSE endpoint directly:"
Write-Host "   curl -N `"http://localhost:3000/api/v1/stream-logs/request/$requestId`""

Write-Host "`n💡 Quick fix attempts:" -ForegroundColor Cyan
Write-Host "1. Restart the agent for this session"
Write-Host "2. Refresh the Live Logs page"
Write-Host "3. Check if the session status is actually 'running'"
Write-Host "4. Verify the request_id is correct and matches an active agent"

Write-Host "`n✅ Debug complete!" -ForegroundColor Green

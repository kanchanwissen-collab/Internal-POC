# Test the API server and new SSE endpoint

Write-Host "🧪 Testing API Server SSE Endpoint" -ForegroundColor Cyan
Write-Host "=" * 50

$requestId = "597e433d-f3f9-4cd9-ba71-4c2b8deef68b"

# Test 1: Check if API server is running
Write-Host "`n1. Testing API Server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✅ API server is running (Status: $($response.StatusCode))" -ForegroundColor Green
    $apiRunning = $true
} catch {
    Write-Host "   ❌ API server not accessible: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 Try: docker-compose up -d api_server" -ForegroundColor Yellow
    $apiRunning = $false
}

if ($apiRunning) {
    # Test 2: Check if new SSE endpoint exists
    Write-Host "`n2. Testing new SSE endpoint..." -ForegroundColor Yellow
    $sseUrl = "http://localhost:8000/api/v1/stream-logs/request/$requestId"
    Write-Host "   🔗 URL: $sseUrl"
    
    try {
        $response = Invoke-WebRequest -Uri $sseUrl -UseBasicParsing -TimeoutSec 10 -Headers @{
            "Accept" = "text/event-stream"
            "Cache-Control" = "no-cache"
        }
        
        Write-Host "   ✅ SSE endpoint responded (Status: $($response.StatusCode))" -ForegroundColor Green
        Write-Host "   📋 Headers: $($response.Headers.Keys -join ', ')" -ForegroundColor Gray
        
        if ($response.Content) {
            Write-Host "   📝 Response preview:" -ForegroundColor Gray
            $response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)) | Write-Host -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "   ❌ SSE endpoint error: $($_.Exception.Message)" -ForegroundColor Red
        
        # Check if it's a 404 (endpoint doesn't exist) or other error
        if ($_.Exception.Message -like "*404*") {
            Write-Host "   💡 The new endpoint may not be available yet." -ForegroundColor Yellow
            Write-Host "   💡 Try restarting the API server to pick up the new code:" -ForegroundColor Yellow
            Write-Host "      docker-compose restart api_server" -ForegroundColor Cyan
        }
    }
    
    # Test 3: Check what endpoints are available
    Write-Host "`n3. Checking available endpoints..." -ForegroundColor Yellow
    try {
        $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
        $content = $docsResponse.Content
        
        if ($content -like "*stream-logs*") {
            Write-Host "   ✅ Found stream-logs endpoints in API docs" -ForegroundColor Green
            
            if ($content -like "*stream-logs/request*") {
                Write-Host "   ✅ New request-based endpoint is available!" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️ Only batch-based endpoint found" -ForegroundColor Yellow
                Write-Host "   💡 Need to restart API server to pick up new endpoint" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ❌ No stream-logs endpoints found" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "   ❌ Could not check API docs: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Summary and next steps
Write-Host "`n" + "=" * 50
Write-Host "🔧 Summary and Next Steps:" -ForegroundColor Cyan

if (-not $apiRunning) {
    Write-Host "`n❌ API server is not running" -ForegroundColor Red
    Write-Host "📋 To fix:" -ForegroundColor Yellow
    Write-Host "   1. docker-compose up -d api_server" -ForegroundColor White
    Write-Host "   2. Wait for startup, then retry this test" -ForegroundColor White
} else {
    Write-Host "`n✅ API server is running" -ForegroundColor Green
    Write-Host "📋 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Restart API server to pick up new SSE endpoint:" -ForegroundColor White
    Write-Host "      docker-compose restart api_server" -ForegroundColor Cyan
    Write-Host "   2. Wait a minute for restart" -ForegroundColor White
    Write-Host "   3. Retry the Live Logs in the frontend" -ForegroundColor White
    Write-Host "   4. Check API server logs if issues persist:" -ForegroundColor White
    Write-Host "      docker logs api-server" -ForegroundColor Cyan
}

Write-Host "`n💡 Remember: The frontend should use port 8000 (API server)" -ForegroundColor Blue
Write-Host "   Not port 3000 (frontend's own API routes)" -ForegroundColor Blue
